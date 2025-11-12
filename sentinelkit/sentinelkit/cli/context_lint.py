"""Placeholder context lint CLI."""

from __future__ import annotations

import typer

__all__ = ["run"]


def run(target: str | None = typer.Option(None, "--target", help="Context slug to lint.")) -> None:
    """Run the context lint workflow (stub)."""
    raise NotImplementedError("Context lint CLI is pending implementation.")