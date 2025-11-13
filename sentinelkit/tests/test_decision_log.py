"""Unit tests for the decision ledger helpers."""

from __future__ import annotations

from pathlib import Path

import portalocker
import pytest

from sentinelkit.cli import decision_log
from sentinelkit.cli.decision_log import DecisionLedger, DecisionLedgerError, DecisionPayload

FIXTURE_LEDGER = Path(__file__).parent / "fixtures" / "DECISIONS.sample.md"


def _copy_fixture(tmp_path: Path) -> Path:
    dest = tmp_path / "DECISIONS.md"
    dest.write_text(FIXTURE_LEDGER.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def test_append_updates_ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger_path = _copy_fixture(tmp_path)
    ledger = DecisionLedger(ledger_path)
    monkeypatch.setattr(decision_log, "_git_short_hash", lambda _: "abcdef1")

    payload = DecisionPayload(
        author="Router",
        scope="src/specify_cli",
        decision="Add sentinel decisions command",
        rationale="Python CLI needs provenance logging",
        outputs=["src/specify_cli/cli.py", "DECISIONS.md"],
    )

    result = ledger.append(payload, agent="ROUTER", rules_hash="ROUTER@2.0")

    assert result.id == "D-0003"
    assert result.wrote_ledger is True
    assert (
        result.snippets.plain
        == "ProducedBy=ROUTER RulesHash=ROUTER@2.0 Decision=D-0003 (#abcdef1)"
    )

    updated = ledger_path.read_text(encoding="utf-8")
    assert "## NEXT_ID\nD-0004" in updated
    assert "Decision: Add sentinel decisions command" in updated
    assert updated.strip().endswith(result.entry)


def test_append_dry_run_creates_preview_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger_path = _copy_fixture(tmp_path)
    original = ledger_path.read_text(encoding="utf-8")
    ledger = DecisionLedger(ledger_path)
    monkeypatch.setattr(decision_log, "_git_short_hash", lambda _: "deadbee")

    preview = tmp_path / "preview.md"
    payload = DecisionPayload(
        author="Builder",
        scope=".sentinel/scripts",
        decision="Dry run append",
        rationale="CI diff should not mutate ledger",
        outputs=[".sentinel/scripts/decision.py"],
    )

    result = ledger.append(payload, dry_run=True, output_path=preview)

    assert result.dry_run is True
    assert result.wrote_ledger is False
    assert ledger_path.read_text(encoding="utf-8") == original
    assert preview.exists()
    assert "Dry run append" in preview.read_text(encoding="utf-8")


def test_missing_outputs_raises(tmp_path: Path) -> None:
    ledger_path = _copy_fixture(tmp_path)
    ledger = DecisionLedger(ledger_path)

    payload = DecisionPayload(
        author="Builder",
        scope="docs",
        decision="Invalid payload",
        rationale="outputs missing",
        outputs=[],
    )

    with pytest.raises(DecisionLedgerError):
        ledger.append(payload)


def test_lock_contention_raises_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger_path = _copy_fixture(tmp_path)
    ledger = DecisionLedger(ledger_path, lock_timeout=0.1)
    monkeypatch.setattr(decision_log, "_git_short_hash", lambda _: "deadbee")

    payload = DecisionPayload(
        author="Builder",
        scope="docs",
        decision="Lock contention",
        rationale="ensure error message",
        outputs=["docs/sample.md"],
    )

    with portalocker.Lock(str(ledger.lock_path), timeout=1, mode="w"):
        with pytest.raises(DecisionLedgerError) as excinfo:
            ledger.append(payload)

    assert excinfo.value.payload.code == "decision.lock_timeout"
