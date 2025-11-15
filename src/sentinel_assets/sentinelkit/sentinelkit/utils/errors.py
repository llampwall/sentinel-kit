"""Custom error utilities and normalized payloads."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, MutableMapping

__all__ = ["SentinelKitError", "ErrorPayload", "build_error_payload", "serialize_error"]


@dataclass(slots=True)
class ErrorPayload:
    code: str
    message: str
    remediation: str | None = None
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data["details"] is None:
            data.pop("details")
        if data["remediation"] is None:
            data.pop("remediation")
        return data


class SentinelKitError(RuntimeError):
    """Base exception for SentinelKit."""

    def __init__(self, payload: ErrorPayload) -> None:
        super().__init__(payload.message)
        self.payload = payload


def build_error_payload(
    code: str,
    message: str,
    *,
    remediation: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> ErrorPayload:
    """Factory helper for normalized error payloads."""
    return ErrorPayload(code=code, message=message, remediation=remediation, details=details)


def serialize_error(error: ErrorPayload | SentinelKitError) -> MutableMapping[str, Any]:
    """Return a dict representation for JSON/log output."""
    payload = error.payload if isinstance(error, SentinelKitError) else error
    return payload.to_dict()
