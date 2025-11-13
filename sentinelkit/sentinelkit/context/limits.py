"""Context limits dataclasses + loader."""

from __future__ import annotations

from dataclasses import dataclass
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import jsonschema
import yaml

from sentinelkit.utils.errors import SentinelKitError, build_error_payload

__all__ = [
    "ContextRule",
    "CapsuleRule",
    "ContextLimits",
    "ContextLimitsError",
    "load_context_limits",
]

DEFAULT_CONFIG = Path(".sentinel/context/limits/context-limits.json")
DEFAULT_SCHEMA = Path(".sentinel/context/limits/context-limits.schema.json")


@dataclass(slots=True, frozen=True)
class ContextRule:
    """Artifact rule describing glob targets + enforcement metadata."""

    name: str
    globs: tuple[str, ...]
    max_lines: int | None = None
    enforce_allowed_context: bool = False


@dataclass(slots=True, frozen=True)
class CapsuleRule:
    """Override rule applied to individual capsule paths."""

    pattern: str
    max_lines: int | None = None
    reason: str | None = None


@dataclass(slots=True, frozen=True)
class ContextLimits:
    """Materialized limits configuration."""

    default_max_lines: int
    warning_threshold: float
    forbidden_paths: tuple[str, ...]
    artifacts: tuple[ContextRule, ...]
    overrides: tuple[CapsuleRule, ...]
    config_path: Path
    schema_path: Path

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration for JSON output."""
        return {
            "defaultMaxLines": self.default_max_lines,
            "warningThreshold": self.warning_threshold,
            "forbiddenPaths": list(self.forbidden_paths),
            "artifacts": [
                {
                    "name": rule.name,
                    "globs": list(rule.globs),
                    "maxLines": rule.max_lines,
                    "enforceAllowedContext": rule.enforce_allowed_context,
                }
                for rule in self.artifacts
            ],
            "overrides": [
                {
                    "pattern": override.pattern,
                    "maxLines": override.max_lines,
                    "reason": override.reason,
                }
                for override in self.overrides
            ],
            "configPath": str(self.config_path),
            "schemaPath": str(self.schema_path),
        }


class ContextLimitsError(SentinelKitError):
    """Raised when the limits configuration cannot be loaded."""


def load_context_limits(
    *,
    root: Path | str | None = None,
    config_path: Path | str | None = None,
    schema_path: Path | str | None = None,
) -> ContextLimits:
    """Load and validate the context limit configuration."""

    repo_root = _resolve_root(root)
    config = _resolve_path(repo_root, config_path or DEFAULT_CONFIG)
    schema = _resolve_path(repo_root, schema_path or DEFAULT_SCHEMA)

    raw = _read_config(config)
    validator = _get_validator(schema)
    _validate_payload(raw, validator, config)
    normalized = _normalize_config(raw)
    return ContextLimits(
        default_max_lines=normalized["default_max_lines"],
        warning_threshold=normalized["warning_threshold"],
        forbidden_paths=normalized["forbidden_paths"],
        artifacts=normalized["artifacts"],
        overrides=normalized["overrides"],
        config_path=config,
        schema_path=schema,
    )


def _resolve_root(root: Path | str | None) -> Path:
    if root is None:
        return _auto_repo_root()
    return Path(root).resolve()


def _resolve_path(root: Path, path_like: Path | str) -> Path:
    path = Path(path_like)
    return path if path.is_absolute() else (root / path).resolve()


def _auto_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    raise ContextLimitsError(
        build_error_payload(
            code="CONTEXT_LIMITS_ROOT",
            message="Unable to locate repository root for context limits.",
        )
    )


def _read_config(path: Path) -> Mapping[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ContextLimitsError(
            build_error_payload(
                code="CONTEXT_LIMITS_READ",
                message=f"Unable to read context limit config '{path}': {error}",
            )
        ) from error

    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(text) or {}
        else:
            data = json.loads(text)
    except (yaml.YAMLError, json.JSONDecodeError) as error:
        raise ContextLimitsError(
            build_error_payload(
                code="CONTEXT_LIMITS_PARSE",
                message=f"Failed to parse context limit config '{path}': {error}",
            )
        ) from error

    if not isinstance(data, Mapping):
        raise ContextLimitsError(
            build_error_payload(
                code="CONTEXT_LIMITS_PARSE",
                message="Context limit config must be an object.",
            )
        )
    return data


@lru_cache(maxsize=4)
def _get_validator(schema_path: Path) -> jsonschema.Validator:
    try:
        schema_text = schema_path.read_text(encoding="utf-8")
    except OSError as error:
        raise ContextLimitsError(
            build_error_payload(
                code="CONTEXT_LIMITS_READ",
                message=f"Unable to read context limit schema '{schema_path}': {error}",
            )
        ) from error
    try:
        schema = json.loads(schema_text)
    except json.JSONDecodeError as error:
        raise ContextLimitsError(
            build_error_payload(
                code="CONTEXT_LIMITS_PARSE",
                message=f"Failed to parse context limit schema '{schema_path}': {error}",
            )
        ) from error
    return jsonschema.Draft7Validator(schema)


def _validate_payload(payload: Mapping[str, Any], validator: jsonschema.Validator, config: Path) -> None:
    errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
    if not errors:
        return
    message = "\n".join(f"{list(error.path)} -> {error.message}" for error in errors)
    raise ContextLimitsError(
        build_error_payload(
            code="CONTEXT_LIMITS_VALIDATE",
            message=f"Context limit config failed schema validation ({config}):\n{message}",
        )
    )


def _normalize_config(raw: Mapping[str, Any]) -> dict[str, Any]:
    default_max_lines = int(raw["defaultMaxLines"])
    warning_threshold = float(raw.get("warningThreshold", 0.9))
    if warning_threshold <= 0 or warning_threshold > 1:
        raise ContextLimitsError(
            build_error_payload(
                code="CONTEXT_LIMITS_THRESHOLD",
                message="warningThreshold must be between 0 and 1.",
            )
        )

    forbidden_paths = tuple(_normalize_path(p) for p in _require_sequence(raw["forbiddenPaths"]))

    artifacts = tuple(
        ContextRule(
            name=str(artifact["name"]),
            globs=tuple(_normalize_path(glob) for glob in _require_sequence(artifact["globs"])),
            max_lines=int(artifact["maxLines"]) if "maxLines" in artifact else None,
            enforce_allowed_context=bool(artifact.get("enforceAllowedContext", False)),
        )
        for artifact in _require_sequence(raw["artifacts"])
    )

    overrides_raw = raw.get("overrides") or []
    overrides_seq = _require_sequence(overrides_raw)
    overrides = tuple(
        CapsuleRule(
            pattern=_normalize_path(override["pattern"]),
            max_lines=int(override["maxLines"]) if "maxLines" in override else None,
            reason=str(override["reason"]) if "reason" in override else None,
        )
        for override in overrides_seq
    )

    return {
        "default_max_lines": default_max_lines,
        "warning_threshold": warning_threshold,
        "forbidden_paths": forbidden_paths,
        "artifacts": artifacts,
        "overrides": overrides,
    }


def _normalize_path(value: str) -> str:
    cleaned = value.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    while "//" in cleaned:
        cleaned = cleaned.replace("//", "/")
    return cleaned or "."


def _require_sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    raise ContextLimitsError(
        build_error_payload(
            code="CONTEXT_LIMITS_SCHEMA",
            message="Expected a sequence in context limit config.",
        )
    )
