"""Tests for sentinel CLI selfcheck."""

from __future__ import annotations

import json
from typer.testing import CliRunner

from sentinelkit.cli import main as cli_main
from sentinelkit.cli.executor import CheckResult
from sentinelkit.cli import selfcheck as selfcheck_module
from sentinelkit.cli.state import CLIContext
from sentinelkit.utils.errors import build_error_payload

runner = CliRunner()


def _success_check(context: CLIContext) -> CheckResult:
    return CheckResult(name="contracts", status="ok", duration=0.01, data={"message": "ok"})


def _failure_check(context: CLIContext) -> CheckResult:
    return CheckResult(
        name="contracts",
        status="fail",
        duration=0.02,
        data={"message": "missing"},
        error=build_error_payload(code="contracts.error", message="boom"),
    )


def _pending_check(context: CLIContext) -> CheckResult:
    return CheckResult(name="contracts", status="pending", duration=0.0, data={"message": "skipped"})


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
    assert payload["checks"][0]["status"] == "ok"


def test_selfcheck_failure(monkeypatch):
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _failure_check})
    result = runner.invoke(cli_main.app, ["--root", ".", "selfcheck"])
    assert result.exit_code == 1
    assert "Selfcheck failed" in result.stdout


def test_selfcheck_pending(monkeypatch):
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _pending_check})
    result = runner.invoke(cli_main.app, ["--root", ".", "selfcheck"])
    assert result.exit_code == 0
    assert "pending" in result.stdout.lower()
