"""Shared helpers for CLI selfcheck tests."""

from __future__ import annotations

from typing import Mapping

from sentinelkit.cli.executor import CheckResult
from sentinelkit.utils.errors import ErrorPayload

VALID_STATUSES = {"ok", "pending", "fail"}


def make_check(
    status: str,
    *,
    name: str = "contracts",
    message: str | None = None,
    duration: float = 0.01,
    error: ErrorPayload | None = None,
) -> CheckResult:
    """Return a CheckResult with normalized payload for tests."""
    data = {"message": message} if message is not None else None
    return CheckResult(name=name, status=status, duration=duration, data=data, error=error)


def assert_payload_structure(payload: Mapping[str, object], expected_statuses: Mapping[str, str]) -> None:
    """Assert that the emitted JSON payload has the expected structure."""
    assert "ok" in payload
    environment = payload.get("environment")
    assert isinstance(environment, Mapping)
    assert isinstance(environment.get("root"), str)
    assert isinstance(environment.get("platform"), str)
    assert isinstance(environment.get("python"), str)
    assert isinstance(environment.get("ci"), bool)

    checks = payload.get("checks")
    assert isinstance(checks, list)
    assert len(checks) == len(expected_statuses)
    expected_sorted = dict(sorted(expected_statuses.items()))
    names = [check.get("name") for check in checks]
    assert names == list(expected_sorted.keys())
    for check in checks:
        status = check.get("status")
        assert status in VALID_STATUSES
        assert status == expected_sorted[check.get("name")]
        duration = check.get("duration")
        assert isinstance(duration, (int, float))
        data = check.get("data")
        if data is not None:
            assert isinstance(data, Mapping)
        error = check.get("error")
        if error is not None:
            assert isinstance(error, Mapping)
            assert isinstance(error.get("message"), str)
