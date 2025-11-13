"""Regression test guarding users.v1 email format."""

from __future__ import annotations

import re
from pathlib import Path

from sentinelkit.contracts.api import ContractValidator
from sentinelkit.contracts.loader import ContractLoader

FIXTURE_PATH = Path(".sentinel/contracts/fixtures/users.v1/get_active.json")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def test_users_v1_emails_are_rfc_valid(
    contract_loader: ContractLoader,
    contract_validator: ContractValidator,
) -> None:
    result = contract_validator.validate_fixture("users.v1", FIXTURE_PATH)
    assert result.ok, f"Fixture validation errors: {result.errors}"

    payload = contract_loader.load_fixture(FIXTURE_PATH)
    invalid_records = [record for record in payload if not EMAIL_REGEX.match(record["email"])]
    assert not invalid_records, f"Invalid email records detected: {invalid_records}"
