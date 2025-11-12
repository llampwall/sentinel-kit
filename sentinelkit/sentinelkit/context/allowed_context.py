"""Allowed context discovery placeholder."""

from __future__ import annotations

from typing import Sequence

__all__ = ["discover_allowed_context"]


def discover_allowed_context(paths: Sequence[str] | None = None) -> None:
    """Inspect project context directories (not yet implemented)."""
    raise NotImplementedError("Allowed context discovery is pending implementation.")