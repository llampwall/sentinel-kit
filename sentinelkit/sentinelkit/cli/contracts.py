"""Contracts CLI namespace."""

from __future__ import annotations

import typer

from .state import get_context

app = typer.Typer(help="Contracts tooling (placeholder).")


@app.command("validate", help="Validate Sentinel contracts.")
def validate(ctx: typer.Context) -> None:
    """Placeholder contract validation command."""
    _ = get_context(ctx)
    raise NotImplementedError("Contract validation is not implemented yet.")
