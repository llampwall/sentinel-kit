"""Placeholder contract validation CLI."""

from __future__ import annotations

import typer

__all__ = ["run"]


def run(path: str | None = typer.Option(None, "--path", help="Optional contract path.")) -> None:
    """Validate Sentinel contracts (stub)."""
    raise NotImplementedError("Contract validation CLI is pending implementation.")