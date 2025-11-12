"""Decision log CLI namespace."""

from __future__ import annotations

import typer

from .state import get_context

app = typer.Typer(help="Decision log utilities (placeholder).")


@app.command("append", help="Append to the decision log.")
def append(ctx: typer.Context) -> None:
    """Placeholder decision log command."""
    _ = get_context(ctx)
    raise NotImplementedError("Decision log integration is not implemented yet.")
