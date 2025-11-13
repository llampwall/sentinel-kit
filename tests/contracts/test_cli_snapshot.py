from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sentinelkit.cli import main as cli_main

runner = CliRunner()


def test_cli_validate_matches_snapshot(tmp_path: Path) -> None:
    root = _create_sample_contracts(tmp_path)
    result = runner.invoke(
        cli_main.app,
        ["--root", str(root), "--format", "json", "contracts", "validate"],
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    payload = _normalize_paths(payload, root)

    snapshot_path = Path("tests/contracts/snapshots/sample_full.json")
    expected = _load_snapshot(snapshot_path)
    assert payload == expected


def _create_sample_contracts(tmp_path: Path) -> Path:
    contracts_dir = tmp_path / ".sentinel" / "contracts"
    fixtures_dir = contracts_dir / "fixtures" / "sample"
    fixtures_dir.mkdir(parents=True)

    contracts_dir.mkdir(parents=True, exist_ok=True)
    contracts_dir.joinpath("sample.yaml").write_text(
        "contract: sample\nschema:\n  type: object\n  properties:\n    value:\n      type: integer\n  required:\n    - value\n",
        encoding="utf-8",
    )
    fixtures_dir.joinpath("valid.json").write_text(
        '{"metadata":{"ProducedBy":"ProducedBy=CLI RulesHash=CLI@1.0 Decision=D-0001"},"value":1}',
        encoding="utf-8",
    )
    fixtures_dir.joinpath("invalid.json").write_text(
        '{"metadata":{"ProducedBy":"ProducedBy=CLI RulesHash=CLI@1.0 Decision=D-0001"}}',
        encoding="utf-8",
    )
    fixtures_dir.joinpath("missing.json").write_text('{"metadata":{}}', encoding="utf-8")
    return tmp_path


def _load_snapshot(path: Path) -> dict:
    data = json.loads(path.read_text())
    return data


def _normalize_paths(payload: dict, root: Path) -> dict:
    root_posix = str(root).replace("\\", "/")

    def replace(item):
        if isinstance(item, str):
            normalized = item.replace("\\", "/")
            return normalized.replace(root_posix, "{{ROOT}}")
        if isinstance(item, dict):
            return {k: replace(v) for k, v in item.items()}
        if isinstance(item, list):
            return [replace(v) for v in item]
        return item

    return replace(payload)
