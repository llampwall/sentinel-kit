"""Tests for snippet synchronization helpers."""

from __future__ import annotations

from pathlib import Path

from sentinelkit.scripts.snippets import SnippetMapping, sync_snippets


def test_sync_snippets_updates_markers(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text(
        "<!-- SENTINEL:TEST:start -->\nold\n<!-- SENTINEL:TEST:end -->",
        encoding="utf-8",
    )
    snippet = tmp_path / "snippet.md"
    snippet.write_text("replacement", encoding="utf-8")

    mapping = SnippetMapping(
        marker="SENTINEL:TEST",
        target=Path("doc.md"),
        snippet=Path("snippet.md"),
    )

    updated = sync_snippets(root=tmp_path, mappings=(mapping,))
    assert target in updated
    assert "replacement" in target.read_text(encoding="utf-8")
