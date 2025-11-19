"""Utilities to run MCP smoke tests against the stdio server."""

from __future__ import annotations

import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Mapping, Sequence

Command = Sequence[str]

EXPECTED_TOOLS = {
    "sentinel_contract_validate",
    "sentinel_run",
    "sentinel_decision_log",
}


@dataclass(slots=True)
class SmokeTimeouts:
    """User-configurable timeouts per MCP phase."""

    initialize: float = 5.0
    tools_list: float = 5.0
    tools_call: float = 90.0


@dataclass(slots=True)
class SmokeStep:
    """Individual phase result."""

    name: str
    success: bool
    duration: float
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "success": self.success,
            "duration": self.duration,
            "detail": self.detail,
        }


@dataclass(slots=True)
class SmokeSummary:
    """Aggregate smoke run output."""

    ok: bool
    command: Command
    steps: list[SmokeStep] = field(default_factory=list)
    tool_results: Dict[str, Any] = field(default_factory=dict)
    stderr: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "command": list(self.command),
            "steps": [step.to_dict() for step in self.steps],
            "tool_results": self.tool_results,
            "stderr": self.stderr,
        }


DEFAULT_TIMEOUTS = SmokeTimeouts()


def run_smoke(root: Path, *, timeouts: SmokeTimeouts | None = None) -> SmokeSummary:
    """Entrypoint invoked by the CLI; wraps the async implementation."""

    root = Path(root).resolve()
    try:
        return asyncio.run(_run_smoke(root, timeouts or DEFAULT_TIMEOUTS))
    except OSError as exc:
        step = SmokeStep(name="spawn", success=False, duration=0.0, detail=str(exc))
        return SmokeSummary(ok=False, command=_server_command(), steps=[step])


async def _run_smoke(root: Path, timeouts: SmokeTimeouts) -> SmokeSummary:
    command = _server_command()
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(root),
    )
    stderr_task = asyncio.create_task(_capture_stream(process.stderr))
    client = _JsonRpcClient(process)
    steps: list[SmokeStep] = []
    tool_payloads: dict[str, Any] = {}
    preview_path = _ensure_preview_file(root)
    summary: SmokeSummary | None = None

    try:
        step, _ = await _phase(
            "initialize",
            lambda: client.request("initialize"),
            timeout=timeouts.initialize,
            retries=1,
        )
        steps.append(step)
        if not step.success:
            summary = SmokeSummary(False, command, steps, stderr=None)
            return summary

        await client.notify("notifications/initialized")

        list_step, list_payload = await _phase(
            "tools/list",
            lambda: client.request("tools/list"),
            timeout=timeouts.tools_list,
        )
        steps.append(list_step)
        if not list_step.success:
            summary = SmokeSummary(False, command, steps, stderr=None)
            return summary

        missing = EXPECTED_TOOLS - {tool["name"] for tool in list_payload.get("tools", [])}
        if missing:
            steps.append(
                SmokeStep(
                    name="tools/list:verify",
                    success=False,
                    duration=0.0,
                    detail=f"Missing tools: {', '.join(sorted(missing))}",
                )
            )
            summary = SmokeSummary(False, command, steps, stderr=None)
            return summary

        for tool_name in sorted(EXPECTED_TOOLS):
            arguments = _tool_arguments(tool_name, preview_path.relative_to(root))
            step, payload = await _call_tool(client, tool_name, arguments, timeout=timeouts.tools_call)
            steps.append(step)
            if payload is not None:
                tool_payloads[tool_name] = payload
            if not step.success:
                break

        ok = all(step.success for step in steps)
        summary = SmokeSummary(ok, command, steps, tool_payloads, stderr=None)
    finally:
        await _graceful_shutdown(client)
        await _wait_for_process(process)
        stderr_output = (await stderr_task).strip() or None
        if preview_path.exists():
            preview_path.unlink()
        if summary is None:
            summary = SmokeSummary(False, command, steps, tool_payloads, stderr=None)
        summary.stderr = stderr_output
        if process.returncode and process.returncode != 0:
            reason = f"MCP server exited with {process.returncode}"
            summary.steps.append(SmokeStep(name="server-exit", success=False, duration=0.0, detail=reason))
            summary.ok = False
    return summary


async def _graceful_shutdown(client: "_JsonRpcClient") -> None:
    try:
        await asyncio.wait_for(client.request("shutdown"), timeout=2.0)
    except Exception:
        pass
    try:
        await asyncio.wait_for(client.notify("exit"), timeout=1.0)
    except Exception:
        pass


async def _wait_for_process(process: asyncio.subprocess.Process) -> None:
    if process.stdin:
        process.stdin.close()
        try:
            await process.stdin.wait_closed()
        except Exception:
            pass
    if process.returncode is not None:
        return
    try:
        await asyncio.wait_for(process.wait(), timeout=3.0)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()


async def _capture_stream(stream: asyncio.StreamReader | None) -> str:
    if stream is None:
        return ""
    data = await stream.read()
    return data.decode("utf-8", errors="replace")


def _server_command() -> list[str]:
    return [sys.executable, "-m", "sentinelkit.cli.mcp.server"]


async def _phase(
    name: str,
    action: Callable[[], Awaitable[Any]],
    *,
    timeout: float,
    retries: int = 0,
) -> tuple[SmokeStep, Any]:
    attempt = 0
    detail = None
    while attempt <= retries:
        start = time.perf_counter()
        try:
            result = await asyncio.wait_for(action(), timeout=timeout)
            return SmokeStep(name=name, success=True, duration=time.perf_counter() - start), result
        except asyncio.TimeoutError:
            detail = f"Phase '{name}' timed out after {timeout:.1f}s"
        except Exception as exc:  # pragma: no cover - defensive
            detail = f"{name} failed: {exc}"
        attempt += 1
        if attempt > retries:
            return SmokeStep(name=name, success=False, duration=time.perf_counter() - start, detail=detail), None
    return SmokeStep(name=name, success=False, duration=0.0, detail=detail), None


async def _call_tool(
    client: "_JsonRpcClient",
    tool_name: str,
    arguments: Mapping[str, Any],
    *,
    timeout: float,
) -> tuple[SmokeStep, Any]:
    step, result = await _phase(
        f"tools.call[{tool_name}]",
        lambda: client.request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": dict(arguments),
            },
        ),
        timeout=timeout,
    )
    payload = None
    if result:
        payload = _extract_json_content(result)
        if result.get("isError"):
            step.success = False
            step.detail = result.get("content", [{}])[0].get("text", f"{tool_name} returned error")
    return step, payload


def _extract_json_content(result: Mapping[str, Any]) -> Any:
    for entry in result.get("content", []):
        if entry.get("type") == "json":
            return entry.get("json")
    return result


def _tool_arguments(tool_name: str, preview_path: Path) -> Mapping[str, Any]:
    if tool_name == "sentinel_contract_validate":
        return {}
    if tool_name == "sentinel_run":
        return {}
    if tool_name == "sentinel_decision_log":
        return {
            "author": "MCP_SMOKE",
            "scope": [".sentinel/docs/IMPLEMENTATION.md"],
            "decision": "MCP smoke validation",
            "rationale": "Ensure MCP decision_log tool responds.",
            "outputs": [".sentinel/docs/IMPLEMENTATION.md"],
            "dry_run": True,
            "preview": str(preview_path).replace("\\", "/"),
            "agent": "MCP_SMOKE",
            "rules_hash": "MCP_SMOKE@1.0",
        }
    return {}


def _ensure_preview_file(root: Path) -> Path:
    preview = root / ".sentinel" / "status" / "mcp-smoke-preview.md"
    preview.parent.mkdir(parents=True, exist_ok=True)
    if preview.exists():
        preview.unlink()
    return preview


class _JsonRpcClient:
    """Minimal JSON-RPC client for stdio subprocesses."""

    def __init__(self, process: asyncio.subprocess.Process) -> None:
        if process.stdin is None or process.stdout is None:
            raise RuntimeError("MCP server must expose stdin/stdout pipes.")
        self._process = process
        self._reader = process.stdout
        self._writer = process.stdin
        self._next_id = 0

    async def request(self, method: str, params: Mapping[str, Any] | None = None) -> Any:
        payload = self._build_payload(method, params)
        await self._write(payload)
        message = await self._read()
        if "error" in message:
            error = message["error"]
            raise RuntimeError(f"{method} failed ({error.get('code')}): {error.get('message')}")
        return message.get("result")

    async def notify(self, method: str, params: Mapping[str, Any] | None = None) -> None:
        await self._write(self._build_payload(method, params, include_id=False))

    def _build_payload(
        self,
        method: str,
        params: Mapping[str, Any] | None,
        *,
        include_id: bool = True,
    ) -> dict[str, Any]:
        message: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if include_id:
            self._next_id += 1
            message["id"] = self._next_id
        if params is not None:
            message["params"] = params
        return message

    async def _write(self, payload: Mapping[str, Any]) -> None:
        message_str = json.dumps(payload, separators=(",", ":"))
        print(f"[MCP SMOKE WRITE] {message_str}", file=sys.stderr, flush=True)
        encoded = (message_str + "\n").encode("utf-8")
        self._writer.write(encoded)
        await self._writer.drain()

    async def _read(self) -> Mapping[str, Any]:
        line = await self._reader.readline()
        if not line:
            raise RuntimeError("MCP server closed the connection unexpectedly.")
        try:
            decoded = line.decode("utf-8").rstrip("\r\n")
            print(f"[MCP SMOKE READ RAW] {decoded}", file=sys.stderr, flush=True)
            return json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid MCP response payload: {exc.msg}") from exc
