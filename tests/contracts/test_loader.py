from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "sentinelkit"))
sys.path.append(str(Path(__file__).resolve().parents[2] / "sentinelkit" / "sentinelkit"))

import pytest

from sentinelkit.contracts.loader import ContractLoader


def create_schema(path: Path, *, name: str | None = None) -> None:
    payload = {"contract": name or path.stem, "schema": {"type": "object"}}
    path.write_text(
        f"contract: {payload['contract']}\nschema:\n  type: object\n",
        encoding="utf-8",
    )


def create_fixture(path: Path, *, produced_by: str = "ProducedBy=CLI RulesHash=CLI@1.0 Decision=D-0001") -> None:
    payload = {"metadata": {"ProducedBy": produced_by}, "data": {}}
    path.write_text('{"metadata":{"ProducedBy":"%s"},"data":{}}' % produced_by, encoding="utf-8")


def test_load_schemas_sorted_and_named(tmp_path: Path) -> None:
    contracts_dir = tmp_path / ".sentinel" / "contracts"
    fixtures_dir = contracts_dir / "fixtures"
    fixtures_dir.mkdir(parents=True)

    create_schema(contracts_dir / "b.yaml", name="beta")
    create_schema(contracts_dir / "a.yaml", name="alpha")

    loader = ContractLoader(root=tmp_path)
    schemas = loader.load_schemas()
    assert list(schemas.keys()) == ["alpha", "beta"]
    assert schemas["alpha"].path.name == "a.yaml"


def test_load_schemas_cache_and_force_reload(tmp_path: Path) -> None:
    contracts_dir = tmp_path / ".sentinel" / "contracts"
    fixtures_dir = contracts_dir / "fixtures"
    fixtures_dir.mkdir(parents=True)

    target = contracts_dir / "contract.yaml"
    create_schema(target, name="alpha")

    loader = ContractLoader(root=tmp_path)
    schemas = loader.load_schemas()
    assert schemas["alpha"].schema["type"] == "object"

    # update schema
    target.write_text("contract: alpha\nschema:\n  type: array\n", encoding="utf-8")
    schemas_again = loader.load_schemas()
    assert schemas_again["alpha"].schema["type"] == "object"

    schemas_force = loader.load_schemas(force_reload=True)
    assert schemas_force["alpha"].schema["type"] == "array"


def test_iter_fixtures_sorted(tmp_path: Path) -> None:
    contracts_dir = tmp_path / ".sentinel" / "contracts"
    fixtures_parent = contracts_dir / "fixtures"
    (fixtures_parent / "b").mkdir(parents=True)
    (fixtures_parent / "a").mkdir(parents=True)

    create_fixture(fixtures_parent / "b" / "2.json")
    create_fixture(fixtures_parent / "a" / "1.json")
    create_fixture(fixtures_parent / "a" / "3.json")

    loader = ContractLoader(root=tmp_path)
    fixtures = list(loader.iter_fixtures())
    assert [f.relative_to(fixtures_parent) for f in fixtures] == [
        Path("a/1.json"),
        Path("a/3.json"),
        Path("b/2.json"),
    ]


def test_iter_contract_fixtures_filters(tmp_path: Path) -> None:
    contracts_dir = tmp_path / ".sentinel" / "contracts"
    fixtures_parent = contracts_dir / "fixtures"
    (fixtures_parent / "users").mkdir(parents=True)
    (fixtures_parent / "orders").mkdir(parents=True)

    target = fixtures_parent / "users" / "active.json"
    create_fixture(target)
    create_fixture(fixtures_parent / "orders" / "new.json")

    loader = ContractLoader(root=tmp_path)
    pairs = list(loader.iter_contract_fixtures(contract_id="users"))
    assert pairs == [("users", target)]

    pairs = list(loader.iter_contract_fixtures(fixture_path=target))
    assert pairs == [("users", target)]


def test_resolve_fixture_outside_root(tmp_path: Path) -> None:
    (tmp_path / ".sentinel" / "contracts" / "fixtures").mkdir(parents=True)
    loader = ContractLoader(root=tmp_path)
    with pytest.raises(FileNotFoundError):
        next(loader.iter_contract_fixtures(fixture_path="missing.json"))
