from __future__ import annotations

from pathlib import Path

import pytest

from sentinelkit.contracts.loader import ContractLoader
from sentinelkit.contracts.api import ContractValidator


def write_schema(path: Path, *, name: str) -> None:
    path.write_text(
        f"contract: {name}\nschema:\n  type: object\n  properties:\n    value:\n      type: integer\n  required:\n    - value\n",
        encoding="utf-8",
    )


def write_fixture(path: Path, *, value: int | None) -> None:
    if value is None:
        payload = (
            '{"metadata":{"ProducedBy":"ProducedBy=CLI RulesHash=CLI@1.0 Decision=D-0001"},'
            '"other":"data"}'
        )
    else:
        payload = (
            '{"metadata":{"ProducedBy":"ProducedBy=CLI RulesHash=CLI@1.0 Decision=D-0001"},'
            f'"value": {value}' + "}"
        )
    path.write_text(payload, encoding="utf-8")


def setup_contracts(tmp_path: Path) -> ContractValidator:
    contracts_dir = tmp_path / ".sentinel" / "contracts"
    fixtures_dir = contracts_dir / "fixtures" / "sample"
    fixtures_dir.mkdir(parents=True)
    write_schema(contracts_dir / "sample.yaml", name="sample")
    write_fixture(fixtures_dir / "valid.json", value=42)
    write_fixture(fixtures_dir / "invalid.json", value=None)
    loader = ContractLoader(root=tmp_path)
    return ContractValidator(loader)


def test_validate_fixture_success(tmp_path: Path) -> None:
    validator = setup_contracts(tmp_path)
    fixture = tmp_path / ".sentinel" / "contracts" / "fixtures" / "sample" / "valid.json"
    result = validator.validate_fixture("sample", fixture)
    assert result.ok
    assert result.errors == []


def test_validate_fixture_failure(tmp_path: Path) -> None:
    validator = setup_contracts(tmp_path)
    fixture = tmp_path / ".sentinel" / "contracts" / "fixtures" / "sample" / "invalid.json"
    result = validator.validate_fixture("sample", fixture)
    assert not result.ok
    assert result.errors and result.errors[0].schema_path == "required"


def test_validate_all(tmp_path: Path) -> None:
    validator = setup_contracts(tmp_path)
    results = validator.validate_all()
    assert len(results) == 2
    assert any(not r.ok for r in results)


def test_missing_produced_by(tmp_path: Path) -> None:
    validator = setup_contracts(tmp_path)
    fixture = tmp_path / ".sentinel" / "contracts" / "fixtures" / "sample" / "missing.json"
    fixture.write_text('{"metadata": {}}', encoding="utf-8")
    result = validator.validate_fixture("sample", fixture)
    assert not result.ok
    assert result.errors and "ProducedBy" in result.errors[0].message
