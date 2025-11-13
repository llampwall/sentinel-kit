"""Tests for sentinel CLI selfcheck."""

from __future__ import annotations

import json
from typing import Dict

from typer.testing import CliRunner

from sentinelkit.cli import main as cli_main
from sentinelkit.cli.executor import CheckResult
from sentinelkit.cli import selfcheck as selfcheck_module
from sentinelkit.cli.state import CLIContext
from sentinelkit.utils.errors import build_error_payload

runner = CliRunner()


def _success_check(context: CLIContext) -> CheckResult:
    return CheckResult(name="contracts", success=True, duration=0.01, data={"message": "ok"})


def _failure_check(context: CLIContext) -> CheckResult:
    return CheckResult(
        name="contracts",
        success=False,
        duration=0.02,
        data={"message": "missing"},
        error=build_error_payload(code="contracts.error", message="boom"),
    )


def test_selfcheck_pretty_success(monkeypatch):
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _success_check})
    result = runner.invoke(cli_main.app, ["--root", ".", "selfcheck"])
    assert result.exit_code == 0
    assert "Selfcheck OK" in result.stdout


def test_selfcheck_json_success(monkeypatch):
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _success_check})
    result = runner.invoke(cli_main.app, ["--root", ".", "--format", "json", "selfcheck"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["checks"][0]["name"] == "contracts"


def test_selfcheck_failure(monkeypatch):
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _failure_check})
    result = runner.invoke(cli_main.app, ["--root", ".", "selfcheck"])
    assert result.exit_code == 1
    assert "Selfcheck failed" in result.stdout
