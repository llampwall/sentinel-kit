"""Sentinel selfcheck command (placeholder)."""

from __future__ import annotations

import typer

from .state import get_context

__all__ = ["run"]


def run(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show additional diagnostics."),
) -> None:
    """Run SentinelKit self diagnostics (stub implementation)."""
    context = get_context(ctx)
    message = f"Sentinel selfcheck is not implemented yet (root={context.root})."
    if verbose:
        message += " No diagnostics were run."
    typer.echo(message)
