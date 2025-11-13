"""Deterministic contract loader for schemas and fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator

import yaml

__all__ = ["ContractLoader", "ContractSchema"]


@dataclass(slots=True)
class ContractSchema:
    name: str
    schema: dict
    path: Path


class ContractLoader:
    """Loads sentinel contract schemas and fixtures with deterministic ordering."""

    def __init__(
        self,
        *,
        root: Path | None = None,
        contracts_dir: Path | None = None,
        fixtures_dir: Path | None = None,
    ) -> None:
        self.root = root or Path.cwd()
        self.contracts_dir = contracts_dir or self.root / ".sentinel" / "contracts"
        self.fixtures_dir = fixtures_dir or self.contracts_dir / "fixtures"
        self._schema_cache: Dict[str, ContractSchema] = {}

    def load_schemas(self, *, force_reload: bool = False) -> Dict[str, ContractSchema]:
        """Load and cache schema definitions."""
        if not force_reload and self._schema_cache:
            return self._schema_cache

        self._schema_cache.clear()
        if not self.contracts_dir.exists():
            raise FileNotFoundError(f"Contracts directory not found: {self.contracts_dir}")

        for file_path in sorted(self.contracts_dir.glob("*.yaml")):
            schema = self._load_yaml(file_path)
            name = schema.get("contract") or file_path.stem
            definition = schema.get("schema") or schema
            self._schema_cache[name] = ContractSchema(name=name, schema=definition, path=file_path)

        return self._schema_cache

    def get_schema(self, contract_id: str, *, force_reload: bool = False) -> ContractSchema:
        schemas = self.load_schemas(force_reload=force_reload)
        if contract_id not in schemas:
            raise KeyError(f"Contract schema '{contract_id}' not found.")
        return schemas[contract_id]

    def iter_fixtures(self, contract_id: str | None = None) -> Iterator[Path]:
        """Yield fixture paths in deterministic order."""
        if not self.fixtures_dir.exists():
            return iter(())

        contracts = (
            [contract_id]
            if contract_id
            else [p.name for p in sorted(self.fixtures_dir.iterdir()) if p.is_dir()]
        )

        def fixture_iter() -> Iterator[Path]:
            for contract in contracts:
                contract_dir = self.fixtures_dir / contract
                if not contract_dir.is_dir():
                    continue
                for fixture in sorted(contract_dir.glob("*.json")):
                    yield fixture

        return fixture_iter()

    def iter_contract_fixtures(
        self,
        *,
        contract_id: str | None = None,
        fixture_path: Path | None = None,
    ) -> Iterator[tuple[str, Path]]:
        """Yield (contract_id, fixture_path) pairs honoring filters."""
        if fixture_path:
            resolved = self._resolve_fixture_path(fixture_path)
            contract = resolved.parent.name
            if contract_id and contract != contract_id:
                return iter(())
            return iter([(contract, resolved)])

        def generator() -> Iterator[tuple[str, Path]]:
            for fixture in self.iter_fixtures(contract_id):
                yield fixture.parent.name, fixture

        return generator()

    def _resolve_fixture_path(self, path: Path | str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.fixtures_dir / candidate
        candidate = candidate.resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"Fixture not found: {candidate}")
        if self.fixtures_dir not in candidate.parents:
            raise ValueError("Fixture path must reside within the fixtures directory.")
        return candidate

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        try:
            return yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse YAML schema '{path}': {exc}") from exc

    @staticmethod
    def load_fixture(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))
