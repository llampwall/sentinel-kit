"""End-to-end CLI tests covering capsule, prompts, snippets, and sentinel runs."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sentinelkit.cli.main import app

runner = CliRunner()


def test_capsule_generate_cli(tmp_path: Path) -> None:
    spec_dir = _create_spec(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "capsule",
            "generate",
            str(spec_dir),
            "--decision",
            "D-1234",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "# Capsule sample-feature@" in result.stdout


def test_prompts_render_cli(tmp_path: Path) -> None:
    capsule = _prepare_prompt_workspace(tmp_path)
    base_args = ["--root", str(tmp_path), "prompts", "render", "--capsule", str(capsule)]

    router_result = runner.invoke(app, [*base_args, "--mode", "router"])
    assert router_result.exit_code == 0, router_result.output
    assert "Available Agents" in router_result.stdout

    agent_result = runner.invoke(app, [*base_args, "--mode", "capsule", "--agent", "builder"])
    assert agent_result.exit_code == 0, agent_result.output
    assert "You are **Builder**" in agent_result.stdout


def test_snippets_sync_cli(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "<!-- SENTINEL:CAPSULES:start -->\nold\n<!-- SENTINEL:CAPSULES:end -->",
        encoding="utf-8",
    )
    snippet_dir = tmp_path / ".sentinel/snippets"
    snippet_dir.mkdir(parents=True)
    (snippet_dir / "capsules.md").write_text("replacement", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "snippets",
            "sync",
            "--marker",
            "SENTINEL:CAPSULES",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "replacement" in readme.read_text(encoding="utf-8")


def test_sentinels_run_cli(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "README.md").write_text("# Fixture\n", encoding="utf-8")
    test_file = workspace / "tests/sentinels/test_cli_smoke.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        "def test_cli_sentinel():\n    assert True\n",
        encoding="utf-8",
    )
    artifacts = workspace / "artifacts"
    json_report = artifacts / "sentinels.json"
    junit_report = artifacts / "sentinels.xml"
    result = runner.invoke(
        app,
        [
            "--root",
            str(workspace),
            "sentinels",
            "run",
            "--json-report",
            str(json_report),
            "--junit",
            str(junit_report),
        ],
    )
    assert result.exit_code == 0, result.output
    summary = json.loads(json_report.read_text(encoding="utf-8"))
    assert summary["ok"] is True
    junit_content = junit_report.read_text(encoding="utf-8")
    assert "<testsuite" in junit_content


def test_selfcheck_json_output() -> None:
    result = runner.invoke(
        app,
        [
            "--format",
            "json",
            "selfcheck",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    sentinel_check = next(check for check in payload["checks"] if check["name"] == "sentinels")
    assert sentinel_check["success"] is True


def test_agents_roster_cli(tmp_path: Path) -> None:
    _prepare_prompt_workspace(tmp_path)
    result = runner.invoke(
        app,
        [
            "--root",
            str(tmp_path),
            "--format",
            "json",
            "agents",
            "roster",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    ids = {agent["id"] for agent in payload["agents"]}
    assert "builder" in ids
    assert "router" in ids


# helpers --------------------------------------------------------------------


def _create_spec(root: Path) -> Path:
    readme = root / "README.md"
    readme.write_text("# Fixture README\n", encoding="utf-8")
    template_dir = root / ".sentinel/templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    (template_dir / "capsule.md").write_text(
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
    spec_dir = root / "specs/sample-feature"
    spec_dir.mkdir(parents=True, exist_ok=True)
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


def _prepare_prompt_workspace(root: Path) -> Path:
    readme = root / "README.md"
    readme.write_text("# Fixture README\n", encoding="utf-8")

    limits_dir = root / ".sentinel/context/limits"
    limits_dir.mkdir(parents=True, exist_ok=True)
    limits_config = {
        "defaultMaxLines": 400,
        "warningThreshold": 0.9,
        "forbiddenPaths": [".git"],
        "artifacts": [
            {
                "name": "fixture-capsule",
                "globs": [
                    "specs/sample/capsule.md"
                ],
                "enforceAllowedContext": True,
                "maxLines": 400
            }
        ],
    }
    (limits_dir / "context-limits.json").write_text(json.dumps(limits_config), encoding="utf-8")
    schema_path = Path(".sentinel/context/limits/context-limits.schema.json")
    (limits_dir / "context-limits.schema.json").write_text(schema_path.read_text(encoding="utf-8"), encoding="utf-8")

    def _create_agent(name: str, role: str, playbook: str) -> None:
        agent_dir = root / ".sentinel/agents" / name
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "agent.json").write_text(
            json.dumps(
                {
                    "id": name,
                    "name": name.title(),
                    "rulesHash": f"{name.upper()}@1.0",
                    "summary": f"{name} summary",
                    "routing_keywords": ["test"],
                    "mount_paths": ["src/**"],
                    "prompt_files": [
                        f".sentinel/agents/{name}/ROLE.md",
                        f".sentinel/agents/{name}/PLAYBOOK.md",
                    ],
                }
            ),
            encoding="utf-8",
        )
        (agent_dir / "ROLE.md").write_text(role, encoding="utf-8")
        (agent_dir / "PLAYBOOK.md").write_text(playbook, encoding="utf-8")

    _create_agent("builder", "## Role\n- build", "## Playbook\n- steps")
    _create_agent("router", "Router role", "Router playbook")

    capsule_dir = root / "specs/sample"
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
