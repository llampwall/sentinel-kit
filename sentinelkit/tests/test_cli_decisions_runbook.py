"""CLI integration tests for decision and runbook commands."""

from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from sentinelkit.cli.main import app

FIXTURE_LEDGER = Path(__file__).parent / "fixtures" / "DECISIONS.sample.md"

runner = CliRunner()


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".sentinel").mkdir(parents=True)
    (root / ".sentinel" / "docs").mkdir(parents=True)
    shutil.copy(FIXTURE_LEDGER, root / ".sentinel" / "DECISIONS.md")
    (root / ".sentinel" / "docs" / "IMPLEMENTATION.md").write_text("# Implementation Notes\n", encoding="utf-8")
    return root


def test_decision_append_command(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(root),
            "decisions",
            "append",
            "--author",
            "Builder",
            "--scope",
            ".sentinel/scripts",
            "--decision",
            "Document CLI commands",
            "--rationale",
            "Automation requires provenance and snippets.",
            "--outputs",
            "README.md",
        ],
    )

    assert result.exit_code == 0, result.stdout
    ledger = (root / ".sentinel" / "DECISIONS.md").read_text(encoding="utf-8")
    assert "Document CLI commands" in ledger
    assert "ProducedBy=" in result.stdout


def test_decision_append_dry_run(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    ledger = root / ".sentinel" / "DECISIONS.md"
    original = ledger.read_text(encoding="utf-8")
    preview = root / "preview.md"

    result = runner.invoke(
        app,
        [
            "--root",
            str(root),
            "--format",
            "json",
            "decisions",
            "append",
            "--author",
            "Router",
            "--scope",
            ".sentinel/scripts",
            "--decision",
            "Dry run decision",
            "--rationale",
            "Dry run test",
            "--outputs",
            "README.md",
            "--dry-run",
            "--output",
            str(preview),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert ledger.read_text(encoding="utf-8") == original
    assert preview.exists()
    payload = result.stdout.strip()
    assert '"dry_run": true' in payload


def test_runbook_append_command(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(root),
            "runbook",
            "append",
            "--section",
            "stack",
            "--note",
            "uv-only runtime replaces Node.",
            "--author",
            "Router",
            "--timestamp",
            "2025-11-13T12:00Z",
        ],
    )

    assert result.exit_code == 0, result.stdout
    text = (root / ".sentinel" / "docs" / "IMPLEMENTATION.md").read_text(encoding="utf-8")
    assert "## Stack Context" in text
    assert "uv-only runtime replaces Node." in text


def test_runbook_append_dry_run(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    runbook = root / ".sentinel" / "docs" / "IMPLEMENTATION.md"
    original = runbook.read_text(encoding="utf-8")
    preview = root / "runbook-preview.md"

    result = runner.invoke(
        app,
        [
            "--root",
            str(root),
            "--format",
            "json",
            "runbook",
            "append",
            "--section",
            "gaps",
            "--note",
            "Decision CLI dry run recorded.",
            "--author",
            "Observer",
            "--dry-run",
            "--output",
            str(preview),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert runbook.read_text(encoding="utf-8") == original
    assert preview.exists()
    assert '"dry_run": true' in result.stdout
