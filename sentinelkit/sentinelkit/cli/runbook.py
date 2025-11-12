"""Runbook CLI namespace."""

from __future__ import annotations

import typer

from .state import get_context

app = typer.Typer(help="Runbook helpers (placeholder).")


@app.command("show", help="Print runbook status.")
def show(ctx: typer.Context) -> None:
    """Placeholder runbook command."""
    context = get_context(ctx)
    typer.echo(f"Runbook tooling is not implemented yet (root={context.root}).")
