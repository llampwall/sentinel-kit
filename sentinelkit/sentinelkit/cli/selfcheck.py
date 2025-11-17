"""Sentinel selfcheck command."""

from __future__ import annotations

import json
import time
from typing import Dict, Mapping

import typer
from rich.console import Console
from rich.table import Table

from sentinelkit.cli.mcp.smoke import SmokeSummary, run_smoke
from sentinelkit.utils.errors import build_error_payload

from .executor import CheckResult, run_checks
from .state import CLIContext, get_context
from .sentinels import run_sentinel_pytest

__all__ = ["run"]


def run(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show additional diagnostics."),
) -> None:
    """Run SentinelKit self diagnostics."""
    context = get_context(ctx)
    checks = _build_checks()
    results = sorted(run_checks(context, checks, show_status=not verbose), key=lambda r: r.name)
    ok = all(result.status != "fail" for result in results)
    has_pending = any(result.status == "pending" for result in results)

    if context.format == "json":
        payload = {
            "ok": ok,
            "environment": {
                "root": str(context.root),
                "ci": context.env.is_ci,
                "platform": context.env.platform,
                "python": context.env.python_version,
            },
            "checks": [result.to_dict() for result in results],
        }
        typer.echo(json.dumps(payload, indent=2))
    else:
        console = Console()
        console.print(_build_table(results))
        if not ok:
            summary = "[bold red]Selfcheck failed[/bold red]"
        elif has_pending:
            summary = "[bold yellow]Selfcheck OK (pending checks)[/bold yellow]"
        else:
            summary = "[bold green]Selfcheck OK[/bold green]"
        console.print(summary)

    if not ok:
        raise typer.Exit(1)


def _build_table(results: list[CheckResult]) -> Table:
    table = Table(title="Sentinel selfcheck")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Duration", justify="right")
    table.add_column("Details")

    icon_map = {"ok": "✅", "pending": "⏳", "fail": "❌"}
    for result in results:
        status_icon = icon_map.get(result.status, result.status)
        status = f"{status_icon} {result.status}"
        details = result.data.get("message") if result.data else ""
        if result.error:
            err = result.error.message
            if result.error.remediation:
                err += f" ({result.error.remediation})"
            details = err
        table.add_row(result.name, status, f"{result.duration:.2f}s", details or "-")
    return table


def _build_checks() -> Dict[str, callable]:
    return {
        "contracts": _placeholder_check(
            "contracts", "Contract validation not configured yet. Add schemas to enable this gate."
        ),
        "context": _placeholder_check(
            "context", "Context lint not configured yet. Copy context budgets to enable this gate."
        ),
        "capsule": _placeholder_check(
            "capsule", "Capsule generator dry-run not configured yet. Add capsule metadata to enable this gate."
        ),
        "sentinels": _sentinel_check,
        "mcp": _mcp_check,
    }


def _placeholder_check(name: str, message: str):
    def runner(context: CLIContext) -> CheckResult:
        data = {"message": message, "root": str(context.root)}
        return CheckResult(name=name, status="pending", duration=0.0, data=data)

    return runner


def _sentinel_check(context: CLIContext) -> CheckResult:
    """Run sentinel pytest suite and surface status."""

    tests_dir = context.root / "tests" / "sentinels"
    if not tests_dir.exists() or not any(tests_dir.rglob("test_*.py")):
        return CheckResult(
            name="sentinels",
            status="pending",
            duration=0.0,
            data={
                "message": "No sentinel pytest suite configured yet.",
                "tests_path": str(tests_dir),
            },
        )

    start = time.perf_counter()
    try:
        exit_code, summary = run_sentinel_pytest(root=context.root, quiet=True)
        status = "ok" if exit_code == 0 else "fail"
        error = None
        if status == "fail":
            error = build_error_payload(code="sentinels.failed", message="Sentinel tests failed.")
        return CheckResult(
            name="sentinels",
            status=status,
            duration=time.perf_counter() - start,
            data=summary,
            error=error,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return CheckResult(
            name="sentinels",
            status="fail",
            duration=time.perf_counter() - start,
            error=build_error_payload(code="sentinels.error", message=str(exc)),
        )


def _mcp_check(context: CLIContext) -> CheckResult:
    """Run MCP smoke tests and surface status."""

    start = time.perf_counter()
    summary = run_smoke(context.root)
    duration = time.perf_counter() - start
    data = summary.to_dict()
    if summary.ok:
        return CheckResult(name="mcp", status="ok", duration=duration, data=data)

    pending_reason = _diagnose_mcp_pending(summary, context)
    if pending_reason:
        pending_data = dict(data)
        pending_data.setdefault("status", "pending")
        pending_data.setdefault("message", pending_reason)
        return CheckResult(name="mcp", status="pending", duration=duration, data=pending_data)

    failed_step = next((step for step in summary.steps if not step.success), None)
    detail = failed_step.detail if failed_step else "MCP smoke failed."
    error = build_error_payload(
        code="mcp.failed",
        message=detail or "MCP smoke failed.",
        remediation="Run `uvx sentinel mcp smoke --timeout-call 60` for more detail.",
        details={"failed_step": failed_step.name if failed_step else None},
    )
    return CheckResult(name="mcp", status="fail", duration=duration, data=data, error=error)


def _diagnose_mcp_pending(summary: SmokeSummary, context: CLIContext) -> str | None:
    """Return a skip reason when MCP is not configured for this workspace."""

    config_file = context.root / ".mcp.json"
    if not config_file.exists():
        return "MCP client configuration (.mcp.json) not found; configure your IDE before enabling the smoke test."

    decision_log_payload = summary.tool_results.get("mcp.sentinel.decision_log")
    if isinstance(decision_log_payload, Mapping):
        error = decision_log_payload.get("error")
        if isinstance(error, Mapping):
            code = error.get("code")
            if code == "decision.ledger_missing":
                ledger_path = context.root / ".sentinel" / "DECISIONS.md"
                return f"Sentinel decision ledger missing ({ledger_path}). Copy DECISIONS.md before running MCP smoke."
    return None
