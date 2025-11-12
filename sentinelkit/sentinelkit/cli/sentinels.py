"""Sentinel regression CLI namespace."""

from __future__ import annotations

import typer

from .state import get_context

app = typer.Typer(help="Sentinel regression helpers (placeholder).")


@app.command("run", help="Run sentinel pytest suites.")
def run(ctx: typer.Context) -> None:
    """Placeholder sentinel runner command."""
    _ = get_context(ctx)
    raise NotImplementedError("Sentinel pytest integration is not implemented yet.")
