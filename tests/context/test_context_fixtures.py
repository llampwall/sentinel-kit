"""Regression tests for real fixture capsules under .sentinel/context/fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinelkit.context.lint import lint_context

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / ".sentinel/context/fixtures/capsules"
FIXTURE_CONFIG = ".sentinel/context/fixtures/context-limits.fixture.json"
SCHEMA_PATH = ".sentinel/context/limits/context-limits.schema.json"


def capsule(name: str) -> Path:
    target = FIXTURE_DIR / name
    if not target.exists():
        pytest.fail(f"Fixture capsule '{name}' is missing (looked in {target})")
    return target


def run_lint(name: str, **kwargs):
    return lint_context(
        root=REPO_ROOT,
        capsules=[capsule(name)],
        config_path=FIXTURE_CONFIG,
        schema_path=SCHEMA_PATH,
        **kwargs,
    )


def test_line_budget_warns_when_nearing_limit() -> None:
    summary = run_lint("line-299.md")
    assert summary.errors == 0
    assert summary.warnings == 1
    assert {diag.code for diag in summary.diagnostics} == {"NEAR_LIMIT"}


def test_line_budget_warns_at_limit() -> None:
    summary = run_lint("line-300.md")
    assert summary.errors == 0
    assert summary.warnings == 1
    assert {diag.code for diag in summary.diagnostics} == {"NEAR_LIMIT"}


def test_line_budget_fails_at_301_lines() -> None:
    summary = run_lint("line-301.md")
    assert any(diag.code == "MAX_LINES" for diag in summary.diagnostics)
    assert summary.errors == 1


def test_missing_allowed_context_is_error() -> None:
    summary = run_lint("missing-context.md")
    assert summary.errors == 1
    assert {diag.code for diag in summary.diagnostics} == {"MISSING_ALLOWED_CONTEXT"}


def test_invalid_and_missing_includes_surface_clear_errors() -> None:
    escape_summary = run_lint("escape.md")
    assert {diag.code for diag in escape_summary.diagnostics} == {"INVALID_INCLUDE"}

    missing_summary = run_lint("missing-include.md")
    assert {diag.code for diag in missing_summary.diagnostics} == {"MISSING_INCLUDE"}


def test_forbidden_and_duplicate_includes_are_detected() -> None:
    forbidden_summary = run_lint("forbidden.md")
    assert {diag.code for diag in forbidden_summary.diagnostics} == {"FORBIDDEN_INCLUDE"}

    duplicate_summary = run_lint("duplicate.md")
    assert {diag.code for diag in duplicate_summary.diagnostics} == {"DUPLICATE_INCLUDE"}
    assert duplicate_summary.warnings == 1


def test_diagnostics_are_sorted_deterministically() -> None:
    summary = lint_context(
        root=REPO_ROOT,
        capsules=[
            capsule("line-301.md"),
            capsule("duplicate.md"),
            capsule("forbidden.md"),
        ],
        config_path=FIXTURE_CONFIG,
        schema_path=SCHEMA_PATH,
    )
    ordered = [f"{diag.path}:{diag.code}" for diag in summary.diagnostics]
    assert ordered == sorted(ordered)
