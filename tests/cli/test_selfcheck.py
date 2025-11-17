"""Tests for sentinel CLI selfcheck."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from sentinelkit.cli import main as cli_main
from sentinelkit.cli import selfcheck as selfcheck_module
from sentinelkit.utils.errors import build_error_payload
from sentinelkit.tests._selfcheck_helpers import assert_payload_structure, make_check

runner = CliRunner()


def _invoke_selfcheck(monkeypatch, checks: dict[str, callable], args: list[str]) -> str:
    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: checks)
    result = runner.invoke(cli_main.app, args)
    assert result.exit_code == 0, result.stdout
    return result.stdout


@pytest.mark.parametrize(
    ("status", "expected_exit", "expected_phrase"),
    [
        ("ok", 0, "Selfcheck OK"),
        ("pending", 0, "pending checks"),
        ("fail", 1, "Selfcheck failed"),
    ],
)
def test_pretty_mode_exit_codes(monkeypatch, status: str, expected_exit: int, expected_phrase: str) -> None:
    def _check(_context):
        error = None
        if status == "fail":
            error = build_error_payload(code="contracts.error", message="boom")
        return make_check(status=status, message=status, error=error)

    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"contracts": _check})
    result = runner.invoke(cli_main.app, ["--root", ".", "selfcheck"])
    assert result.exit_code == expected_exit
    assert expected_phrase in result.stdout


def test_json_payload_structure_and_statuses(monkeypatch) -> None:
    checks = {
        "capsule": lambda _context: make_check(status="pending", name="capsule", message="todo", duration=0.0),
        "sentinels": lambda _context: make_check(status="ok", name="sentinels", message="pass", duration=0.02),
    }
    stdout = _invoke_selfcheck(monkeypatch, checks, ["--root", ".", "--format", "json", "selfcheck"])
    payload = json.loads(stdout)
    assert_payload_structure(payload, {"capsule": "pending", "sentinels": "ok"})
    messages = {check["name"]: check["data"]["message"] for check in payload["checks"] if check.get("data")}
    assert messages["capsule"] == "todo"
    assert messages["sentinels"] == "pass"


def test_json_payload_includes_errors(monkeypatch) -> None:
    error = build_error_payload(code="sentinels.failed", message="pytest failed")

    def _failing_check(_context):
        return make_check(status="fail", name="sentinels", error=error)

    monkeypatch.setattr(selfcheck_module, "_build_checks", lambda: {"sentinels": _failing_check})
    result = runner.invoke(cli_main.app, ["--root", ".", "--format", "json", "selfcheck"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_payload_structure(payload, {"sentinels": "fail"})
    check_payload = payload["checks"][0]
    assert check_payload["error"]["message"] == "pytest failed"
