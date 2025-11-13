"""Tests for sentinelkit.context.lint."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinelkit.context.lint import ContextLintError, lint_context

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = "tests/context/fixtures/context_limits/lint-config.json"
SCHEMA_PATH = ".sentinel/context/limits/context-limits.schema.json"
CAPSULE_DIR = Path("tests/context/fixtures/capsules")


def capsule(name: str) -> Path:
    return CAPSULE_DIR / f"{name}.md"


def test_lint_context_reports_expected_diagnostics() -> None:
    summary = lint_context(root=REPO_ROOT, config_path=CONFIG_PATH, schema_path=SCHEMA_PATH)

    assert summary.checked_files == 4
    codes = {diag.code for diag in summary.diagnostics}
    assert codes == {
        "MAX_LINES",
        "MISSING_ALLOWED_CONTEXT",
        "NEAR_LIMIT",
        "INVALID_INCLUDE",
        "MISSING_INCLUDE",
        "FORBIDDEN_INCLUDE",
        "DUPLICATE_INCLUDE",
    }


def test_lint_context_capsule_filter_limits_results() -> None:
    summary = lint_context(
        root=REPO_ROOT,
        config_path=CONFIG_PATH,
        schema_path=SCHEMA_PATH,
        capsules=[capsule("valid")],
    )

    assert summary.checked_files == 1
    assert summary.diagnostics == ()


def test_lint_context_strict_flag_controls_failure() -> None:
    summary = lint_context(
        root=REPO_ROOT,
        config_path=CONFIG_PATH,
        schema_path=SCHEMA_PATH,
        capsules=[capsule("warning")],
    )
    assert summary.warnings == 1
    assert summary.errors == 0
    assert not summary.strict
    assert not summary.should_fail()

    strict_summary = lint_context(
        root=REPO_ROOT,
        config_path=CONFIG_PATH,
        schema_path=SCHEMA_PATH,
        capsules=[capsule("warning")],
        strict=True,
    )
    assert strict_summary.strict
    assert strict_summary.should_fail()


def test_lint_context_blocks_capsule_outside_root() -> None:
    with pytest.raises(ContextLintError):
        lint_context(
            root=REPO_ROOT,
            config_path=CONFIG_PATH,
            schema_path=SCHEMA_PATH,
            capsules=["../capsules/outside.md"],
        )
