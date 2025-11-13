"""Golden snapshot tests for the prompt renderer."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from sentinelkit.prompt.render import PromptRenderer

FIXTURE_ROOT = Path("tests/fixtures/prompts_snapshot")
SCHEMA_PATH = Path(".sentinel/context/limits/context-limits.schema.json")


def test_prompt_renderer_matches_snapshot(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(FIXTURE_ROOT / "workspace", workspace)

    renderer = PromptRenderer(
        root=workspace,
        config_path=workspace / ".sentinel/context/limits/context-limits.json",
        schema_path=SCHEMA_PATH,
    )
    capsule_path = workspace / "specs/sample/capsule.md"

    router_prompt = renderer.render_router_prompt(capsule_path)
    expected_router = (FIXTURE_ROOT / "expected_router_prompt.md").read_text(encoding="utf-8")
    assert router_prompt == expected_router

    builder_prompt = renderer.render_agent_prompt(capsule_path, "builder")
    expected_builder = (FIXTURE_ROOT / "expected_builder_prompt.md").read_text(encoding="utf-8")
    assert builder_prompt == expected_builder

    payload_path = workspace / "router.json"
    payload_path.write_text(
        json.dumps(
            {
                "leadAgent": "builder",
                "requiredOutputs": ["Implement feature"],
                "contextToMount": ["README.md"],
                "acceptanceCriteria": [],
                "notes": "route decision",
            }
        ),
        encoding="utf-8",
    )
    log_path = renderer.write_router_log(capsule_path, payload_path)
    assert log_path.exists()
