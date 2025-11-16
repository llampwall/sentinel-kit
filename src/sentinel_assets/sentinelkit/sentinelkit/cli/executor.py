"""Concurrency helpers for running sentinel checks."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Sequence

from rich.console import Console
from rich.status import Status

from .state import CLIContext
from sentinelkit.utils.errors import ErrorPayload, serialize_error

__all__ = ["CheckResult", "run_checks"]

CheckStatus = Literal["ok", "pending", "fail"]


@dataclass(slots=True)
class CheckResult:
    name: str
    status: CheckStatus
    duration: float
    data: dict | None = None
    error: ErrorPayload | None = None

    def to_dict(self) -> dict:
        payload = {
            "name": self.name,
            "status": self.status,
            "duration": self.duration,
        }
        if self.data is not None:
            payload["data"] = self.data
        if self.error is not None:
            payload["error"] = serialize_error(self.error)
        return payload


CheckCallable = Callable[[CLIContext], CheckResult]


def run_checks(
    context: CLIContext,
    checks: Mapping[str, CheckCallable],
    *,
    show_status: bool = True,
) -> Sequence[CheckResult]:
    """Execute each check concurrently and return structured results."""
    console = Console()
    results: list[CheckResult] = []

    status: Status | None = None
    if show_status and context.format == "pretty":
        status = console.status("Running sentinel checks...")
        status.start()

    try:
        with ThreadPoolExecutor(max_workers=len(checks)) as executor:
            future_map = {
                executor.submit(_run_single_check, name, fn, context): name for name, fn in checks.items()
            }
            for future in as_completed(future_map):
                result = future.result()
                results.append(result)
                if status:
                    status_icon = {
                        "ok": "✅",
                        "pending": "⏳",
                        "fail": "❌",
                    }.get(result.status, "❔")
                    status.update(f"[bold]{result.name}[/] {status_icon}")
    finally:
        if status:
            status.stop()

    return results


def _run_single_check(name: str, fn: CheckCallable, context: CLIContext) -> CheckResult:
    start = time.perf_counter()
    try:
        return fn(context)
    except Exception as exc:  # pragma: no cover - placeholder until real checks land
        payload = ErrorPayload(code=f"{name}.error", message=str(exc))
        return CheckResult(name=name, status="fail", duration=time.perf_counter() - start, error=payload)
