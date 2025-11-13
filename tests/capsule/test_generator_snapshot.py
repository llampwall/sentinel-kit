"""Golden snapshot tests for the capsule generator."""

from __future__ import annotations

from pathlib import Path

from sentinelkit.capsule.generator import CapsuleGenerator

FIXTURE_SPEC = Path("tests/fixtures/capsule_snapshot/spec")
EXPECTED = Path("tests/fixtures/capsule_snapshot/expected_capsule.md")


def test_capsule_generator_matches_snapshot() -> None:
    generator = CapsuleGenerator(root=Path("."))
    result = generator.generate(spec_dir=FIXTURE_SPEC, decision="D-TEST", write=False)
    assert result.content == EXPECTED.read_text(encoding="utf-8")
