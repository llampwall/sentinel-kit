"""Sentinel selfcheck command (placeholder)."""

from __future__ import annotations

import typer

__all__ = ["run"]


def run(verbose: bool = typer.Option(False, "--verbose", "-v", help="Show additional diagnostics.")) -> None:
    """Run SentinelKit self diagnostics (stub implementation)."""
    message = "Sentinel selfcheck is not implemented yet."
    if verbose:
        message += " No diagnostics were run."
    typer.echo(message)
