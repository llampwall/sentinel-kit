"""Prompts CLI namespace."""

from __future__ import annotations

import typer

from .state import get_context

app = typer.Typer(help="Prompt rendering utilities (placeholder).")


@app.command("render", help="Render Sentinel prompts.")
def render(ctx: typer.Context) -> None:
    """Placeholder prompt render command."""
    _ = get_context(ctx)
    raise NotImplementedError("Prompt rendering is not implemented yet.")
