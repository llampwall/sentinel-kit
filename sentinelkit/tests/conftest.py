"""Shared test fixtures for sentinelkit package tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_LEDGER = Path(__file__).parent / "fixtures" / "DECISIONS.sample.md"


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    """Seed a minimal repository structure used by MCP-related tests."""
    sentinel_dir = tmp_path / ".sentinel"
    contracts_dir = sentinel_dir / "contracts"
    fixtures_dir = contracts_dir / "fixtures" / "sample.v1"
    tests_dir = tmp_path / "tests" / "sentinels"

    contracts_dir.mkdir(parents=True)
    fixtures_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    (contracts_dir / "sample.v1.yaml").write_text(
        """
contract: sample.v1
schema:
  type: object
  required: ["metadata", "value"]
  properties:
    metadata:
      type: object
      required: ["ProducedBy"]
      properties:
        ProducedBy:
          type: string
    value:
      type: integer
""".strip(),
        encoding="utf-8",
    )

    (fixtures_dir / "ok.json").write_text(
        '{"metadata": {"ProducedBy": "TEST-AGENT"}, "value": 42}',
        encoding="utf-8",
    )

    (tests_dir / "test_sample.py").write_text(
        "def test_sample() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    (sentinel_dir / "DECISIONS.md").write_text(
        FIXTURE_LEDGER.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    return tmp_path
