"""Regression tests for sentinel CLI selfcheck behavior."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from sentinelkit.cli import main as cli_main
from sentinelkit.cli import selfcheck as selfcheck_module
from sentinelkit.cli.executor import CheckResult
from sentinelkit.cli.state import CLIContext
from sentinelkit.utils.errors import build_error_payload

runner = CliRunner()


def _ok_check(_context: CLIContext) -> CheckResult:
    return CheckResult(name="contracts", status="ok", duration=0.01, data={"message": "ok"})


def _pending_check(_context: CLIContext) -> CheckResult:
    return CheckResult(name="contracts", status="pending", duration=0.0, data={"message": "todo"})


def _failing_check(_context: CLIContext) -> CheckResult:
    return CheckResult(
        name="contracts",
        status="fail",
        duration=0.01,
        error=build_error_payload(code="contracts.error", message="boom"),
    )


def test_json_payload_includes_status(monkeypatch):
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _ok_check})
    result = runner.invoke(cli_main.app, ["--format", "json", "selfcheck"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["checks"][0]["status"] == "ok"


def test_exit_code_zero_with_pending(monkeypatch):
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _pending_check})
    result = runner.invoke(cli_main.app, ["selfcheck"])
    assert result.exit_code == 0, result.output


def test_exit_code_nonzero_on_failure(monkeypatch):
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _failing_check})
    result = runner.invoke(cli_main.app, ["selfcheck"])
    assert result.exit_code == 1
