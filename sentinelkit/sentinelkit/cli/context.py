"""Context CLI namespace."""

from __future__ import annotations

import typer

from .state import get_context

app = typer.Typer(help="Context linting and utilities (placeholder).")


@app.command("lint", help="Run the allowed-context linter.")
def lint(ctx: typer.Context) -> None:
    """Placeholder context lint command."""
    _ = get_context(ctx)
    raise NotImplementedError("Context linting is not implemented yet.")
