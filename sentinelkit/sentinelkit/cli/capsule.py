"""Capsule CLI namespace."""

from __future__ import annotations

import typer

from .state import get_context

app = typer.Typer(help="Capsule generation helpers (placeholder).")


@app.command("generate", help="Generate capsules from specs.")
def generate(ctx: typer.Context) -> None:
    """Placeholder capsule generation command."""
    _ = get_context(ctx)
    raise NotImplementedError("Capsule generation is not implemented yet.")
