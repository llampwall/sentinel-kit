"""Placeholder decision log CLI."""

from __future__ import annotations

import typer

__all__ = ["run"]


def run(message: str = typer.Argument(..., help="Decision rationale.")) -> None:
    """Append to the decision log (stub)."""
    raise NotImplementedError("Decision log CLI is pending implementation.")