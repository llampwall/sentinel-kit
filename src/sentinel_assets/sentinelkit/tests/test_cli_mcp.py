"""CLI integration tests for MCP commands."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sentinelkit.cli import selfcheck as selfcheck_module
from sentinelkit.cli.main import app
from sentinelkit.cli.mcp.smoke import SmokeStep, SmokeSummary
from sentinelkit.cli.state import CLIContext, EnvironmentInfo

runner = CliRunner()


def test_mcp_smoke_command(repo_root: Path) -> None:
    result = runner.invoke(
        app,
        [
            "--root",
            str(repo_root),
            "--format",
            "json",
            "mcp",
            "smoke",
            "--timeout-call",
            "10",
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert set(payload["tool_results"]) == {
        "mcp.sentinel.contract_validate",
        "mcp.sentinel.decision_log",
        "mcp.sentinel.sentinel_run",
    }
    preview_file = repo_root / ".sentinel" / "status" / "mcp-smoke-preview.md"
    assert not preview_file.exists()


def test_selfcheck_reports_mcp_success(monkeypatch, repo_root: Path) -> None:
    summary = SmokeSummary(
        ok=True,
        command=["python", "-m", "sentinelkit.cli.mcp.server"],
        steps=[SmokeStep(name="initialize", success=True, duration=0.01)],
        tool_results={},
    )
    monkeypatch.setattr(selfcheck_module, "run_smoke", lambda root, *_, **__: summary)

    context = CLIContext(
        root=repo_root,
        format="pretty",
        env=EnvironmentInfo(is_ci=False, platform="test", python_version="3.12"),
    )
    result = selfcheck_module._build_checks()["mcp"](context)

    assert result.status == "ok"
    assert result.data["command"] == summary.command


def test_selfcheck_reports_mcp_failure(monkeypatch, repo_root: Path) -> None:
    failure_step = SmokeStep(name="tools.call[mcp.sentinel.decision_log]", success=False, duration=0.5, detail="preview lock")
    summary = SmokeSummary(
        ok=False,
        command=["python", "-m", "sentinelkit.cli.mcp.server"],
        steps=[
            SmokeStep(name="initialize", success=True, duration=0.01),
            failure_step,
        ],
        tool_results={},
    )
    monkeypatch.setattr(selfcheck_module, "run_smoke", lambda root, *_, **__: summary)

    context = CLIContext(
        root=repo_root,
        format="pretty",
        env=EnvironmentInfo(is_ci=True, platform="test", python_version="3.12"),
    )
    result = selfcheck_module._build_checks()["mcp"](context)

    assert result.status == "fail"
    assert result.error
    assert result.error.message == failure_step.detail
