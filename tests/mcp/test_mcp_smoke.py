"""Repo-level MCP smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_repo_mcp_smoke_cli(repo_root: Path) -> None:
    """Invoke the Sentinel MCP smoke CLI and ensure it exercises the Python server."""

    command = [
        sys.executable,
        "-m",
        "sentinelkit.cli.main",
        "--root",
        str(repo_root),
        "--format",
        "json",
        "mcp",
        "smoke",
        "--timeout-call",
        "90",
    ]
    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert set(payload["tool_results"]) == {
        "sentinel_contract_validate",
        "sentinel_run",
        "sentinel_decision_log",
    }
