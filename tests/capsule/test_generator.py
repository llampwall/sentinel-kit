"""Tests for the Python capsule generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinelkit.capsule.generator import CapsuleGenerator, CapsuleGeneratorError

FIXTURE_SPEC = Path("tests/fixtures/specs/sample-feature")


def test_generate_capsule_writes_output(tmp_path: Path) -> None:
    spec_dir = _prepare_fixture(tmp_path)
    generator = CapsuleGenerator(root=tmp_path)
    result = generator.generate(spec_dir=spec_dir, decision="D-9999", agent="ROUTER")
    assert result.path.exists()
    assert "# Capsule sample-feature@" in result.content
    assert "Allowed Context" in result.content


def test_generate_capsule_respects_line_budget(tmp_path: Path) -> None:
    spec_dir = _prepare_fixture(tmp_path)
    long_goal = "\n".join(f"Line {i}" for i in range(400))
    (spec_dir / "spec.md").write_text(f"# Feature\n\n## Goal\n{long_goal}\n", encoding="utf-8")
    generator = CapsuleGenerator(root=tmp_path)
    with pytest.raises(CapsuleGeneratorError):
        generator.generate(spec_dir=spec_dir, decision="D-0001")


def _prepare_fixture(tmp_path: Path) -> Path:
    readme = tmp_path / "README.md"
    readme.write_text("# Workspace README\n", encoding="utf-8")
    template = tmp_path / ".sentinel/templates"
    template.mkdir(parents=True, exist_ok=True)
    (template / "capsule.md").write_text(
        """{{PRODUCED_BY}}

# Capsule {{CAPSULE_ID}}

## Goal
{{GOAL}}

## Required Outputs
{{REQUIRED_OUTPUTS}}

## Acceptance Criteria
{{ACCEPTANCE_CRITERIA}}

## Allowed Context
{{ALLOWED_CONTEXT}}

## Router Notes
{{ROUTER_NOTES}}
""",
        encoding="utf-8",
    )
    spec_dir = tmp_path / "sample-feature"
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text(
        """# Feature

## Goal
Ship feature quickly.
""",
        encoding="utf-8",
    )
    (spec_dir / "plan.md").write_text(
        """# Plan

## Router Notes
- hand off to ROUTER

## Allowed Context Seeds
- README.md
""",
        encoding="utf-8",
    )
    (spec_dir / "tasks.md").write_text(
        """# Tasks

## Required Outputs
- output A

## Acceptance Criteria
- passes tests
""",
        encoding="utf-8",
    )
    return spec_dir
