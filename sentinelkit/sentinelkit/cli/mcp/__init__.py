"""MCP helpers for SentinelKit."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from ..state import get_context
from . import server
from .smoke import DEFAULT_TIMEOUTS, SmokeTimeouts, run_smoke

app = typer.Typer(help="SentinelKit MCP utilities.")


@app.command("server", help="Launch the MCP stdio server.")
def launch(ctx: typer.Context) -> None:
    """Start the asyncio MCP server rooted at the provided repository path."""
    context = get_context(ctx)
    server.serve(root=context.root)


@app.command("smoke", help="Run initialize/list/call smoke tests against the MCP server.")
def smoke(
    ctx: typer.Context,
    timeout_initialize: Annotated[
        float,
        typer.Option(
            "--timeout-initialize",
            help="Seconds to wait for the initialize response.",
        ),
    ] = DEFAULT_TIMEOUTS.initialize,
    timeout_list: Annotated[
        float,
        typer.Option(
            "--timeout-list",
            help="Seconds to wait for the tools/list response.",
        ),
    ] = DEFAULT_TIMEOUTS.tools_list,
    timeout_call: Annotated[
        float,
        typer.Option(
            "--timeout-call",
            help="Seconds to wait for each tools/call invocation.",
        ),
    ] = DEFAULT_TIMEOUTS.tools_call,
) -> None:
    """Execute a deterministic initialize → tools/list → tools/call sequence."""

    context = get_context(ctx)
    summary = run_smoke(
        context.root,
        timeouts=SmokeTimeouts(
            initialize=timeout_initialize,
            tools_list=timeout_list,
            tools_call=timeout_call,
        ),
    )

    if context.format == "json":
        typer.echo(json.dumps(summary.to_dict(), indent=2))
    else:
        console = Console()
        console.print(_build_summary_table(summary))
        if summary.stderr:
            console.print("[dim]Server stderr:[/dim]")
            console.print(summary.stderr)
        status = "[bold green]MCP smoke passed[/bold green]" if summary.ok else "[bold red]MCP smoke failed[/bold red]"
        console.print(status)

    if not summary.ok:
        raise typer.Exit(1)


def _build_summary_table(summary) -> Table:
    table = Table(title="MCP smoke")
    table.add_column("Step")
    table.add_column("Status")
    table.add_column("Duration", justify="right")
    table.add_column("Detail")
    for step in summary.steps:
        status = "✅" if step.success else "❌"
        detail = step.detail or "-"
        table.add_row(step.name, status, f"{step.duration:.2f}s", detail)
    return table


__all__ = ["app"]
