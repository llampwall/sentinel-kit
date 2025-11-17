"""Contract validation API."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import yaml

from .loader import ContractLoader

__all__ = ["ValidationErrorEntry", "ValidationResult", "ContractValidator"]


@dataclass(slots=True)
class ValidationErrorEntry:
    message: str
    instance_path: str
    schema_path: str
    remediation: str | None = None


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    contract: str
    fixture: Path
    errors: List[ValidationErrorEntry]

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "contract": self.contract,
            "fixture": str(self.fixture),
            "errors": [asdict(error) for error in self.errors],
        }


class ContractValidator:
    def __init__(self, loader: ContractLoader | None = None) -> None:
        self.loader = loader or ContractLoader()
        self.validators: dict[str, Draft202012Validator] = {}

    def validate_fixture(self, contract_id: str, fixture_path: Path) -> ValidationResult:
        schema = self.loader.get_schema(contract_id)
        validator = self._get_validator(contract_id, schema.schema)
        payload = self.loader.load_fixture(fixture_path)
        produced_by_error = self._ensure_produced_by(payload, fixture_path)
        if produced_by_error:
            return ValidationResult(
                ok=False,
                contract=contract_id,
                fixture=fixture_path,
                errors=[produced_by_error],
            )

        errors = [
            ValidationErrorEntry(
                message=error.message,
                instance_path="/".join(error.path),
                schema_path="/".join(str(part) for part in error.schema_path),
            )
            for error in validator.iter_errors(payload)
        ]
        return ValidationResult(
            ok=not errors,
            contract=contract_id,
            fixture=fixture_path,
            errors=errors,
        )

    def validate_all(
        self,
        *,
        contract_id: str | None = None,
        fixture_path: Path | None = None,
    ) -> Sequence[ValidationResult]:
        results: list[ValidationResult] = []
        for contract, fixture in self.loader.iter_contract_fixtures(
            contract_id=contract_id, fixture_path=fixture_path
        ):
            try:
                results.append(self.validate_fixture(contract, fixture))
            except Exception as exc:  # pragma: no cover - surface as validation error
                results.append(
                    ValidationResult(
                        ok=False,
                        contract=contract,
                        fixture=fixture,
                        errors=[
                            ValidationErrorEntry(
                                message=str(exc),
                                instance_path="",
                                schema_path="",
                            )
                        ],
                    )
                )
        return results

    def _get_validator(self, contract_id: str, schema: dict) -> Draft202012Validator:
        if contract_id not in self.validators:
            self.validators[contract_id] = Draft202012Validator(
                schema, format_checker=FormatChecker()
            )
        return self.validators[contract_id]

    @staticmethod
    def _ensure_produced_by(payload: object, source: Path) -> ValidationErrorEntry | None:
        header = None
        if isinstance(payload, list) and payload:
            first = payload[0]
            header = first.get("ProducedBy") or first.get("metadata", {}).get("ProducedBy")
        elif isinstance(payload, dict):
            header = payload.get("metadata", {}).get("ProducedBy") or payload.get("ProducedBy")
        if not isinstance(header, str) or not header.strip():
            return ValidationErrorEntry(
                message=f"Fixture missing ProducedBy header: {source}",
                instance_path="",
                schema_path="ProducedBy",
                remediation="Include ProducedBy=AGENT RulesHash=AGENT@X.Y Decision=D-####",
            )
        return None
