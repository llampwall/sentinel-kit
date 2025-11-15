"""Tests for the runbook updater utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from sentinelkit.runbook.updater import RunbookUpdater, RunbookUpdaterError


def _write_minimal_runbook(path: Path) -> None:
    path.write_text(
        "# Implementation Notes\n\n## Task 0\n- legacy entry\n",
        encoding="utf-8",
    )


def test_append_inserts_sections_and_stack_note(tmp_path: Path) -> None:
    runbook_path = tmp_path / "IMPLEMENTATION.md"
    _write_minimal_runbook(runbook_path)
    updater = RunbookUpdater(runbook_path)

    result = updater.append(
        section="stack",
        note="uv-only runtime replaces the Node workspace.",
        author="Builder",
        timestamp=datetime(2025, 11, 13, 12, 0, tzinfo=timezone.utc),
    )

    assert result.wrote_file is True
    contents = runbook_path.read_text(encoding="utf-8")
    assert contents.index("## Stack Context") < contents.index("## Task 0")
    assert "- [2025-11-13 12:00Z] (Builder) uv-only runtime replaces the Node workspace." in contents
    assert "--section stack --note" not in contents  # placeholder removed for the section


def test_dry_run_writes_preview_only(tmp_path: Path) -> None:
    runbook_path = tmp_path / "IMPLEMENTATION.md"
    original = "# Implementation Notes\n\n## Task 0\n- entry\n"
    runbook_path.write_text(original, encoding="utf-8")
    preview = tmp_path / "preview.md"

    updater = RunbookUpdater(runbook_path)
    result = updater.append(
        section="enforcement",
        note="document contracts/context gates",
        author="Router",
        dry_run=True,
        output_path=preview,
    )

    assert result.wrote_file is False
    assert result.dry_run is True
    assert preview.exists()
    assert "document contracts/context gates" in preview.read_text(encoding="utf-8")
    assert runbook_path.read_text(encoding="utf-8") == original


def test_unknown_section_errors(tmp_path: Path) -> None:
    runbook_path = tmp_path / "IMPLEMENTATION.md"
    _write_minimal_runbook(runbook_path)
    updater = RunbookUpdater(runbook_path)

    with pytest.raises(RunbookUpdaterError):
        updater.append(section="unknown", note="test", author="tester")
