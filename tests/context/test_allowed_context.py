"""Tests for sentinelkit.context.allowed_context."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinelkit.context.allowed_context import (
    AllowedContextError,
    assert_include_exists,
    build_allowed_context,
    discover_allowed_context,
    normalize_include,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "allowed_context"


def test_discover_allowed_context_returns_sorted_entries_with_line_counts() -> None:
    entries = discover_allowed_context(root=FIXTURE_ROOT)
    paths = [entry.relative_path for entry in entries]
    assert paths == [
        ".sentinel/context/background.md",
        ".sentinel/context/guides/primer.md",
    ]

    background = next(entry for entry in entries if entry.relative_path.endswith("background.md"))
    primer = next(entry for entry in entries if entry.relative_path.endswith("primer.md"))

    assert background.line_count == _expected_line_count(FIXTURE_ROOT / ".sentinel/context/background.md")
    assert primer.line_count == _expected_line_count(FIXTURE_ROOT / ".sentinel/context/guides/primer.md")
    assert all("limits" not in entry.relative_path for entry in entries)


def test_discover_allowed_context_deduplicates_and_keeps_seeds() -> None:
    entries = discover_allowed_context(
        paths=["./docs/guide.md", ".sentinel/context/background.md"],
        root=FIXTURE_ROOT,
    )
    paths = [entry.relative_path for entry in entries]
    assert paths.count(".sentinel/context/background.md") == 1
    assert "docs/guide.md" in paths

    guide_entry = next(entry for entry in entries if entry.relative_path == "docs/guide.md")
    assert guide_entry.line_count == _expected_line_count(FIXTURE_ROOT / "docs/guide.md")


def test_normalize_include_blocks_escaping_root() -> None:
    with pytest.raises(AllowedContextError) as excinfo:
        normalize_include(FIXTURE_ROOT, "../outside")
    assert excinfo.value.payload.code == "ALLOWED_CONTEXT_ESCAPE"


def test_assert_include_exists_detects_missing_paths() -> None:
    normalized = normalize_include(FIXTURE_ROOT, "docs/missing.md")
    with pytest.raises(AllowedContextError) as excinfo:
        assert_include_exists(FIXTURE_ROOT, normalized)
    assert excinfo.value.payload.code == "ALLOWED_CONTEXT_MISSING"


def test_build_allowed_context_matches_entry_paths() -> None:
    discover_paths = build_allowed_context(root=FIXTURE_ROOT, seeds=["docs/guide.md"])
    entries = discover_allowed_context(paths=["docs/guide.md"], root=FIXTURE_ROOT)
    assert discover_paths == [entry.relative_path for entry in entries]


def _expected_line_count(path: Path) -> int:
    """Mirror the module's newline counting logic for assertions."""
    text = path.read_text(encoding="utf-8")
    return 0 if not text else text.count("\n") + 1
