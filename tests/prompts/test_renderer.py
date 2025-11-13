"""Tests for the prompt renderer."""

from __future__ import annotations

import json
from pathlib import Path

from sentinelkit.prompt.render import PromptRenderer


def test_render_router_and_agent_prompts(tmp_path: Path) -> None:
    capsule = _prepare_workspace(tmp_path)
    renderer = PromptRenderer(
        root=tmp_path,
        config_path=tmp_path / ".sentinel/context/limits/context-limits.json",
        schema_path=tmp_path / ".sentinel/context/limits/context-limits.schema.json",
    )

    router_prompt = renderer.render_router_prompt(capsule)
    assert "## Capsule" in router_prompt
    assert "Available Agents" in router_prompt

    agent_prompt = renderer.render_agent_prompt(capsule, "builder")
    assert "You are **Builder**" in agent_prompt
    assert "Agent mounts" in agent_prompt

    payload_path = tmp_path / "router.json"
    payload_path.write_text(
        json.dumps(
            {
                "leadAgent": "builder",
                "requiredOutputs": ["foo"],
                "contextToMount": ["README.md"],
                "acceptanceCriteria": [],
                "notes": "test",
            }
        ),
        encoding="utf-8",
    )
    log_path = renderer.write_router_log(capsule, payload_path)
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "builder" in content


def _prepare_workspace(tmp_path: Path) -> Path:
    readme = tmp_path / "README.md"
    readme.write_text("# Fixture README\n", encoding="utf-8")

    limits_dir = tmp_path / ".sentinel/context/limits"
    limits_dir.mkdir(parents=True, exist_ok=True)
    (limits_dir / "context-limits.json").write_text(
        json.dumps(
            {
                "defaultMaxLines": 400,
                "warningThreshold": 0.9,
                "forbiddenPaths": [".git"],
                "artifacts": [
                    {
                        "name": "capsules",
                        "globs": ["specs/sample/capsule.md"],
                        "enforceAllowedContext": True,
                        "maxLines": 400,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    schema_src = Path(".sentinel/context/limits/context-limits.schema.json")
    (limits_dir / "context-limits.schema.json").write_text(schema_src.read_text(encoding="utf-8"), encoding="utf-8")

    agents_dir = tmp_path / ".sentinel/agents/builder"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "agent.json").write_text(
        json.dumps(
            {
                "id": "builder",
                "name": "Builder",
                "rulesHash": "BUILDER@1.0",
                "summary": "Builds features.",
                "routing_keywords": ["build"],
                "mount_paths": ["src/**"],
                "prompt_files": [
                    ".sentinel/agents/builder/ROLE.md",
                    ".sentinel/agents/builder/PLAYBOOK.md",
                ],
            }
        ),
        encoding="utf-8",
    )
    (agents_dir / "ROLE.md").write_text("## Role\n- implement", encoding="utf-8")
    (agents_dir / "PLAYBOOK.md").write_text("## Playbook\n- steps", encoding="utf-8")

    router_dir = tmp_path / ".sentinel/agents/router"
    router_dir.mkdir(parents=True, exist_ok=True)
    (router_dir / "agent.json").write_text(
        json.dumps(
            {
                "id": "router",
                "name": "Router",
                "rulesHash": "ROUTER@1.0",
                "summary": "Routes work.",
                "routing_keywords": [],
                "mount_paths": [],
                "prompt_files": [
                    ".sentinel/agents/router/ROLE.md",
                    ".sentinel/agents/router/PLAYBOOK.md",
                ],
            }
        ),
        encoding="utf-8",
    )
    (router_dir / "ROLE.md").write_text("Router role", encoding="utf-8")
    (router_dir / "PLAYBOOK.md").write_text("Router playbook", encoding="utf-8")

    capsule_dir = tmp_path / "specs/sample"
    capsule_dir.mkdir(parents=True, exist_ok=True)
    capsule = capsule_dir / "capsule.md"
    capsule.write_text(
        """# Capsule sample

## Allowed Context
- README.md

""",
        encoding="utf-8",
    )
    return capsule
