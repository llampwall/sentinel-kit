"""Sentinel selfcheck command."""

from __future__ import annotations

import json
from typing import Dict

import typer
from rich.console import Console
from rich.table import Table

from sentinelkit.utils.errors import build_error_payload

from .executor import CheckResult, run_checks
from .state import CLIContext, get_context

__all__ = ["run"]


def run(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show additional diagnostics."),
) -> None:
    """Run SentinelKit self diagnostics."""
    context = get_context(ctx)
    checks = _build_checks()
    results = sorted(run_checks(context, checks, show_status=not verbose), key=lambda r: r.name)
    ok = all(result.success for result in results)

    console = Console()
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
        console.print(json.dumps(payload, indent=2))
    else:
        console.print(_build_table(results))
        summary = "[bold green]Selfcheck OK[/bold green]" if ok else "[bold red]Selfcheck failed[/bold red]"
        console.print(summary)

    if not ok:
        raise typer.Exit(1)


def _build_table(results: list[CheckResult]) -> Table:
    table = Table(title="Sentinel selfcheck")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Duration", justify="right")
    table.add_column("Details")

    for result in results:
        status = "✅" if result.success else "❌"
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
        "contracts": _placeholder_check("contracts", "Contract validation pending implementation."),
        "context": _placeholder_check("context", "Context lint pending implementation."),
        "capsule": _placeholder_check("capsule", "Capsule generator dry-run pending implementation."),
        "sentinels": _placeholder_check("sentinels", "Sentinel pytest marker pending implementation."),
        "mcp": _placeholder_check("mcp", "MCP smoke tests pending implementation."),
    }


def _placeholder_check(name: str, message: str):
    def runner(context: CLIContext) -> CheckResult:
        data = {"message": message, "root": str(context.root)}
        error = None
        success = False
        if context.env.is_ci:
            error = build_error_payload(code=f"{name}.not_implemented", message=message)
        else:
            success = True
        return CheckResult(name=name, success=success, duration=0.0, data=data, error=error)

    return runner
