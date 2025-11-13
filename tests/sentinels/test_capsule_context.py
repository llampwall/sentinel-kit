"""Regression tests for capsule Allowed Context helper."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinelkit.context.allowed_context import (
    AllowedContextError,
    build_allowed_context,
)


def test_capsule_context_includes_seeds_and_skips_notes(repo_root: Path) -> None:
    allowed = build_allowed_context(
        root=repo_root,
        seeds=[
            ".specify/specs/005-capsule-gen/spec.md",
            ".sentinel/snippets/capsules.md",
        ],
    )
    assert ".specify/specs/005-capsule-gen/spec.md" in allowed
    assert ".sentinel/snippets/capsules.md" in allowed
    assert ".sentinel/docs/IMPLEMENTATION.md" not in allowed


def test_capsule_context_rejects_missing_paths(repo_root: Path) -> None:
    with pytest.raises(AllowedContextError):
        build_allowed_context(root=repo_root, seeds=["docs/DOES-NOT-EXIST.md"])
