"""Asyncio-based MCP stdio server exposing Sentinel tools."""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, BinaryIO, Callable, Dict, Mapping, Sequence

from sentinelkit import get_version
from sentinelkit.cli.decision_log import DecisionLedger, DecisionLedgerError, DecisionPayload
from sentinelkit.cli.sentinels import run_sentinel_pytest
from sentinelkit.contracts.api import ContractValidator
from sentinelkit.contracts.loader import ContractLoader
from sentinelkit.utils.errors import SentinelKitError, serialize_error

__all__ = ["SentinelMCPServer", "serve"]

logger = logging.getLogger(__name__)

JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "2024-11-01"
SERVER_NAME = "sentinel-mcp"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

ToolHandler = Callable[[Mapping[str, Any]], Awaitable["ToolResponse"]] | Callable[[Mapping[str, Any]], "ToolResponse"]


@dataclass(frozen=True)
class ToolSpec:
    """Describe an MCP tool definition and its handler."""

    name: str
    description: str
    input_schema: Mapping[str, Any]
    handler: ToolHandler

    def to_mcp_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": dict(self.input_schema),
        }


@dataclass
class ToolResponse:
    """Represents the payload returned to tools/call."""

    content: Sequence[Mapping[str, Any]]
    is_error: bool = False

    @classmethod
    def from_json(cls, payload: Mapping[str, Any] | Sequence[Any], *, is_error: bool = False) -> "ToolResponse":
        return cls(content=[{"type": "json", "json": payload}], is_error=is_error)

    def to_call_result(self) -> dict[str, Any]:
        result: dict[str, Any] = {"content": list(self.content)}
        if self.is_error:
            result["isError"] = True
        return result


class JsonRpcError(Exception):
    """Structured JSON-RPC error for predictable responses."""

    def __init__(self, code: int, message: str, *, data: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data or {}


class SentinelMCPServer:
    """Core dispatcher that implements JSON-RPC methods."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root or Path.cwd()).resolve()
        self._shutdown_requested = False
        self._exit_requested = False
        loader = ContractLoader(root=self.root)
        self._validator = ContractValidator(loader)
        self._ledger_path = self.root / ".sentinel" / "DECISIONS.md"
        self._tools: Dict[str, ToolSpec] = {
            "mcp.sentinel.contract_validate": ToolSpec(
                name="mcp.sentinel.contract_validate",
                description="Validate fixtures under .sentinel/contracts/fixtures/** against versioned contracts.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "contract": {
                            "type": "string",
                            "description": "Optional contract identifier (e.g., users.v1).",
                        },
                        "fixture": {
                            "type": "string",
                            "description": "Optional path to a single fixture JSON file.",
                        },
                    },
                    "additionalProperties": False,
                },
                handler=self._handle_contract_validate,
            ),
            "mcp.sentinel.sentinel_run": ToolSpec(
                name="mcp.sentinel.sentinel_run",
                description="Execute sentinel-marked pytest suites and return the structured summary.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "marker": {
                            "type": "string",
                            "description": "Optional pytest marker expression (defaults to sentinel suites).",
                        }
                    },
                    "additionalProperties": False,
                },
                handler=self._handle_sentinel_run,
            ),
            "mcp.sentinel.decision_log": ToolSpec(
                name="mcp.sentinel.decision_log",
                description="Append to the Sentinel DECISIONS.md ledger and emit ProducedBy snippets.",
                input_schema={
                    "type": "object",
                    "required": ["author", "scope", "decision", "rationale", "outputs"],
                    "properties": {
                        "author": {"type": "string"},
                        "scope": {
                            "description": "Single scope string or array of scope entries.",
                            "anyOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}},
                            ],
                        },
                        "decision": {"type": "string"},
                        "rationale": {"type": "string"},
                        "outputs": {
                            "description": "One or more output paths touched by the decision.",
                            "anyOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}},
                            ],
                        },
                        "supersedes": {"type": "string"},
                        "decision_id": {"type": "string"},
                        "date": {"type": "string"},
                        "agent": {"type": "string"},
                        "rules_hash": {"type": "string"},
                        "dry_run": {"type": "boolean"},
                        "preview": {
                            "type": "string",
                            "description": "Optional preview path written instead of mutating the ledger.",
                        },
                    },
                    "additionalProperties": False,
                },
                handler=self._handle_decision_log,
            ),
        }

    @property
    def should_exit(self) -> bool:
        return self._exit_requested

    def request_shutdown(self) -> None:
        self._shutdown_requested = True

    async def handle_message(self, request: Mapping[str, Any]) -> Mapping[str, Any] | None:
        method = request.get("method")
        request_id = request.get("id")

        try:
            if method in (None, "notifications/initialized", "$/cancelRequest"):
                return None
            if method == "exit":
                self._exit_requested = True
                return None
            if method == "shutdown":
                self.request_shutdown()
                return self._success(request_id, {})
            if method == "ping":
                return self._success(request_id, {})
            if method == "initialize":
                return self._success(request_id, self._handle_initialize())
            if method == "tools/list":
                return self._success(request_id, {"tools": [tool.to_mcp_dict() for tool in self._tools.values()]})
            if method == "tools/call":
                return self._success(request_id, await self._handle_tools_call(request))
            raise JsonRpcError(METHOD_NOT_FOUND, f"Unsupported method '{method}'.")
        except JsonRpcError as exc:
            if request_id is None:
                return None
            return self._error(request_id, exc)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Unhandled MCP server exception")
            if request_id is None:
                return None
            return self._error(
                request_id,
                JsonRpcError(INTERNAL_ERROR, "Unexpected MCP server failure.", data={"detail": str(exc)}),
            )

    async def _handle_tools_call(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        params = request.get("params")
        if not isinstance(params, Mapping):
            raise JsonRpcError(INVALID_PARAMS, "Missing params for tools/call.")

        name = params.get("name")
        if not isinstance(name, str):
            raise JsonRpcError(INVALID_PARAMS, "Tool name must be provided.")

        spec = self._tools.get(name)
        if spec is None:
            raise JsonRpcError(METHOD_NOT_FOUND, f"Unknown tool '{name}'.")

        arguments = params.get("arguments") or {}
        if not isinstance(arguments, Mapping):
            raise JsonRpcError(INVALID_PARAMS, "Tool arguments must be an object.")

        handler = spec.handler
        if asyncio.iscoroutinefunction(handler):
            response: ToolResponse = await handler(arguments)
        else:
            response = handler(arguments)  # type: ignore[assignment]
        return response.to_call_result()

    def _handle_initialize(self) -> Mapping[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {
                "name": SERVER_NAME,
                "version": get_version(),
            },
            "capabilities": {
                "tools": {
                    "listChanged": False,
                }
            },
        }

    def _handle_contract_validate(self, arguments: Mapping[str, Any]) -> ToolResponse:
        contract_id = self._optional_string(arguments.get("contract"))
        fixture_arg = self._optional_string(arguments.get("fixture"))
        fixture_path = self._resolve_path(fixture_arg) if fixture_arg else None
        results = self._validator.validate_all(contract_id=contract_id, fixture_path=fixture_path)
        summary = {"ok": all(result.ok for result in results), "results": [result.to_dict() for result in results]}
        return ToolResponse.from_json(summary, is_error=not summary["ok"])

    def _handle_sentinel_run(self, arguments: Mapping[str, Any]) -> ToolResponse:
        marker = self._optional_string(arguments.get("marker"))
        exit_code, summary = run_sentinel_pytest(
            root=self.root,
            marker=marker,
            junit=None,
            json_report=None,
            quiet=True,
        )
        summary = dict(summary)
        summary["exit_code"] = int(exit_code)
        summary["marker"] = marker
        return ToolResponse.from_json(summary, is_error=exit_code != 0)

    def _handle_decision_log(self, arguments: Mapping[str, Any]) -> ToolResponse:
        summary: dict[str, Any]
        try:
            payload = DecisionPayload(
                author=self._require_string(arguments.get("author"), "author"),
                scope=self._collapse_scope(arguments.get("scope")),
                decision=self._require_string(arguments.get("decision"), "decision"),
                rationale=self._require_string(arguments.get("rationale"), "rationale"),
                outputs=self._normalize_list(arguments.get("outputs"), label="outputs"),
                supersedes=self._optional_string(arguments.get("supersedes")) or "none",
                date_override=self._optional_string(arguments.get("date")),
            )
            ledger = DecisionLedger(self._ledger_path)
            preview = self._resolve_path(self._optional_string(arguments.get("preview"))) if arguments.get("preview") else None
            result = ledger.append(
                payload,
                agent=self._optional_string(arguments.get("agent")),
                rules_hash=self._optional_string(arguments.get("rules_hash")),
                dry_run=bool(arguments.get("dry_run", False)),
                output_path=preview,
                decision_id=self._optional_string(arguments.get("decision_id")),
            )
            summary = {
                "id": result.id,
                "ledger": str(result.ledger_path),
                "dry_run": result.dry_run,
                "wrote_ledger": result.wrote_ledger,
                "preview": str(result.output_path) if result.output_path else None,
                "snippets": {
                    "plain": result.snippets.plain,
                    "javascript": result.snippets.javascript,
                    "python": result.snippets.python,
                    "markdown": result.snippets.markdown,
                },
            }
            return ToolResponse.from_json(summary)
        except (DecisionLedgerError, SentinelKitError) as error:
            payload = serialize_error(error)
            return ToolResponse.from_json({"ok": False, "error": payload}, is_error=True)

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return str(value)

    @staticmethod
    def _require_string(value: Any, label: str) -> str:
        normalized = SentinelMCPServer._optional_string(value)
        if not normalized:
            raise JsonRpcError(INVALID_PARAMS, f"'{label}' is required.")
        return normalized

    @staticmethod
    def _normalize_list(value: Any, *, label: str) -> list[str]:
        if value is None:
            raise JsonRpcError(INVALID_PARAMS, f"'{label}' is required.")
        if isinstance(value, str):
            items = [entry.strip() for entry in value.split(",") if entry.strip()]
        elif isinstance(value, Sequence):
            items = [str(entry).strip() for entry in value if str(entry).strip()]
        else:
            raise JsonRpcError(INVALID_PARAMS, f"'{label}' must be a string or array.")
        if not items:
            raise JsonRpcError(INVALID_PARAMS, f"At least one value is required for '{label}'.")
        return items

    def _collapse_scope(self, value: Any) -> str:
        entries = self._normalize_list(value, label="scope")
        return ", ".join(entries)

    def _resolve_path(self, value: str | None) -> Path | None:
        if not value:
            return None
        path = Path(value)
        if not path.is_absolute():
            path = (self.root / path).resolve()
        return path

    @staticmethod
    def _success(request_id: Any, result: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": dict(result)}

    @staticmethod
    def _error(request_id: Any, error: JsonRpcError) -> Mapping[str, Any]:
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "error": {
                "code": error.code,
                "message": error.message,
                "data": dict(error.data),
            },
        }


class _StdioTransport:
    """Minimal Content-Length framed transport over stdio pipes."""

    def __init__(self, reader: BinaryIO, writer: BinaryIO) -> None:
        self._reader = reader
        self._writer = writer

    async def read(self) -> Mapping[str, Any] | None:
        loop = asyncio.get_running_loop()
        headers: dict[str, str] = {}
        header_lines: list[str] = []
        while True:
            line = await loop.run_in_executor(None, self._reader.readline)
            if not line:
                if not header_lines:
                    return None
                raise JsonRpcError(INVALID_REQUEST, "Truncated headers.")
            decoded = line.decode("ascii", errors="ignore")
            if decoded in ("\r\n", "\n"):
                break
            header_lines.append(decoded.strip())

        for entry in header_lines:
            if ":" not in entry:
                continue
            name, value = entry.split(":", 1)
            headers[name.strip().lower()] = value.strip()

        if "content-length" not in headers:
            raise JsonRpcError(INVALID_REQUEST, "Missing Content-Length header.")

        try:
            remaining = int(headers["content-length"])
        except ValueError:
            raise JsonRpcError(INVALID_REQUEST, "Invalid Content-Length header.") from None

        if remaining < 0:
            raise JsonRpcError(INVALID_REQUEST, "Negative Content-Length.")

        body = await loop.run_in_executor(None, self._reader.read, remaining)
        if len(body) != remaining:
            raise JsonRpcError(INVALID_REQUEST, "Truncated message body.")

        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise JsonRpcError(PARSE_ERROR, f"Invalid JSON payload: {exc.msg}") from exc

    async def write(self, payload: Mapping[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
        message = header + encoded
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self._writer.write, message)
            await loop.run_in_executor(None, self._writer.flush)
        except BrokenPipeError:  # pragma: no cover - occurs when the client disappears
            pass


async def _serve_async(
    *,
    root: Path | str | None = None,
    reader: BinaryIO | None = None,
    writer: BinaryIO | None = None,
) -> None:
    server = SentinelMCPServer(root=root)
    transport = _StdioTransport(reader or sys.stdin.buffer, writer or sys.stdout.buffer)
    while True:
        try:
            message = await transport.read()
        except JsonRpcError as exc:
            error_payload = SentinelMCPServer._error(None, exc)
            await transport.write(error_payload)
            continue
        if message is None:
            break

        response = await server.handle_message(message)
        if response:
            await transport.write(response)
        if server.should_exit:
            break


def serve(*, root: Path | str | None = None) -> None:
    """Run the JSON-RPC server until the client terminates."""

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, loop.stop)
        except NotImplementedError:  # pragma: no cover - Windows lacks signal handlers for threads
            pass

    try:
        loop.run_until_complete(_serve_async(root=root))
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()


if __name__ == "__main__":  # pragma: no cover
    serve()
