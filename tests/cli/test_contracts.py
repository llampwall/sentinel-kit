from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from sentinelkit.cli import main as cli_main

runner = CliRunner()


def test_contracts_validate_pretty(tmp_path: Path) -> None:
    _create_contract(tmp_path, schema_name="sample", valid_fixture="ok.json")
    result = runner.invoke(
        cli_main.app,
        ["--root", str(tmp_path), "contracts", "validate"],
    )
    assert result.exit_code == 0
    assert "Contract validation" in result.stdout


def test_contracts_validate_json_failure(tmp_path: Path) -> None:
    _create_contract(tmp_path, schema_name="sample", valid_fixture=None)
    result = runner.invoke(
        cli_main.app,
        ["--root", str(tmp_path), "--format", "json", "contracts", "validate"],
    )
    assert result.exit_code == 1
    assert '"ok": false' in result.stdout.lower()


def _create_contract(root: Path, schema_name: str, valid_fixture: str | None) -> None:
    contracts_dir = root / ".sentinel" / "contracts"
    fixtures_dir = contracts_dir / "fixtures" / schema_name
    fixtures_dir.mkdir(parents=True)

    schema_path = contracts_dir / f"{schema_name}.yaml"
    schema_path.write_text(
        f"contract: {schema_name}\nschema:\n  type: object\n  properties:\n    value:\n      type: integer\n  required:\n    - value\n",
        encoding="utf-8",
    )

    payload = (
        '{"metadata":{"ProducedBy":"ProducedBy=CLI RulesHash=CLI@1.0 Decision=D-0001"}, "value": 1}'
        if valid_fixture
        else '{"metadata":{"ProducedBy":"ProducedBy=CLI RulesHash=CLI@1.0 Decision=D-0001"}}'
    )
    fixture_path = fixtures_dir / (valid_fixture or "invalid.json")
    fixture_path.write_text(payload, encoding="utf-8")
