"""Shared pytest fixtures for SentinelKit."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinelkit.contracts.api import ContractValidator
from sentinelkit.contracts.loader import ContractLoader


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Path to the repository root."""

    return Path(".").resolve()


@pytest.fixture(scope="session")
def contract_loader(repo_root: Path) -> ContractLoader:
    """Shared contract loader rooted at the repository."""

    return ContractLoader(root=repo_root)


@pytest.fixture(scope="session")
def contract_validator(contract_loader: ContractLoader) -> ContractValidator:
    """Contract validator backed by the shared loader."""

    return ContractValidator(loader=contract_loader)
