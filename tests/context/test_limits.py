"""Tests for sentinelkit.context.limits."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sentinelkit.context.limits import (
    ContextLimitsError,
    ContextRule,
    CapsuleRule,
    load_context_limits,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CONFIG = "tests/context/fixtures/context_limits/context-limits.json"
SCHEMA_PATH = ".sentinel/context/limits/context-limits.schema.json"
SCHEMA_FILE = (REPO_ROOT / SCHEMA_PATH).resolve()


def test_load_context_limits_parses_artifacts_and_overrides() -> None:
    config = load_context_limits(root=REPO_ROOT, config_path=FIXTURE_CONFIG, schema_path=SCHEMA_PATH)

    assert config.default_max_lines == 300
    assert config.warning_threshold == 0.8
    assert config.forbidden_paths == (".git", "node_modules")
    assert config.config_path.is_absolute()
    assert config.schema_path.is_absolute()

    assert len(config.artifacts) == 2
    capsules_rule = config.artifacts[0]
    router_rule = config.artifacts[1]

    assert isinstance(capsules_rule, ContextRule)
    assert capsules_rule.globs == (".specify/specs/*/capsule.md",)
    assert capsules_rule.max_lines is None
    assert capsules_rule.enforce_allowed_context is True

    assert router_rule.max_lines == 120
    assert router_rule.enforce_allowed_context is False

    assert len(config.overrides) == 1
    override = config.overrides[0]
    assert isinstance(override, CapsuleRule)
    assert override.pattern == ".specify/specs/005-capsule-gen/capsule.md"
    assert override.max_lines == 320
    assert override.reason == "Sample override for docs-heavy capsule"


def test_warning_threshold_defaults_when_missing(tmp_path: Path) -> None:
    config_dir = tmp_path / ".sentinel" / "context" / "limits"
    config_dir.mkdir(parents=True)
    payload = {
        "defaultMaxLines": 200,
        "forbiddenPaths": [".git"],
        "artifacts": [
            {"name": "capsules", "globs": [".specify/specs/*/capsule.md"]}
        ],
    }
    config_file = config_dir / "context-limits.json"
    config_file.write_text(json.dumps(payload), encoding="utf-8")
    config = load_context_limits(
        root=tmp_path,
        config_path=config_file,
        schema_path=SCHEMA_FILE,
    )

    assert config.warning_threshold == 0.9  # default applied
    assert config.default_max_lines == 200


def test_invalid_config_raises_context_limits_error(tmp_path: Path) -> None:
    config_dir = tmp_path / ".sentinel" / "context" / "limits"
    config_dir.mkdir(parents=True)
    payload = {
        "defaultMaxLines": 100,
        "warningThreshold": 1.5,  # Invalid per schema + normalization
        "forbiddenPaths": [".git"],
        "artifacts": [
            {"name": "capsules", "globs": [".specify/specs/*/capsule.md"]}
        ],
    }
    config_file = config_dir / "context-limits.json"
    config_file.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ContextLimitsError) as excinfo:
        load_context_limits(root=tmp_path, config_path=config_file, schema_path=SCHEMA_FILE)

    assert excinfo.value.payload.code in {"CONTEXT_LIMITS_VALIDATE", "CONTEXT_LIMITS_THRESHOLD"}
