"""Tests for Sentinel asset scaffolding inside specify init."""

from __future__ import annotations

from pathlib import Path
import importlib
import subprocess
import sys
import tomllib

import pytest
import typer
from typer.testing import CliRunner

specify_cli = importlib.import_module("specify_cli.__init__")
runner = CliRunner()


def test_apply_sentinel_scaffold_copies_assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, Path]] = []

    def _record_uv(path: Path) -> None:
        calls.append(("uv", path))

    def _record_selfcheck(path: Path) -> None:
        calls.append(("selfcheck", path))

    monkeypatch.setattr(specify_cli, "run_uv_sync_in_project", _record_uv)
    monkeypatch.setattr(specify_cli, "run_sentinel_selfcheck_in_project", _record_selfcheck)

    specify_cli.apply_sentinel_scaffold(tmp_path, tracker=None, assistant="codex")

    assert (tmp_path / "pyproject.toml").exists()
    assert not (tmp_path / "uv.lock").exists()
    assert (tmp_path / ".tool-versions").exists()
    assert (tmp_path / "scripts" / "bootstrap.py").exists()
    assert (tmp_path / "sentinel_project" / "__init__.py").exists()
    assert (tmp_path / "sentinelkit" / "pyproject.toml").exists()
    sentinel_pyproject = tomllib.loads((tmp_path / "sentinelkit" / "pyproject.toml").read_text(encoding="utf-8"))
    include_globs = sentinel_pyproject.get("tool", {}).get("hatch", {}).get("build", {}).get("include", [])
    assert "sentinelkit" in include_globs
    root_pyproject = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    wheel_cfg = (
        root_pyproject.get("tool", {})
        .get("hatch", {})
        .get("build", {})
        .get("targets", {})
        .get("wheel", {})
    )
    assert "packages" in wheel_cfg and "sentinel_project" in wheel_cfg["packages"]
    assert (tmp_path / ".sentinel" / "DECISIONS.md").exists()
    assert (tmp_path / ".sentinel" / "docs" / "IMPLEMENTATION.md").exists()
    assert (tmp_path / ".github" / "workflows" / "sentinel-ci.yml").exists()
    assert (tmp_path / ".codex" / "prompts" / "sentinel.router.md").exists()
    assert ("uv", tmp_path) in calls
    assert ("selfcheck", tmp_path) in calls


def test_specify_init_and_check_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_dir = tmp_path / "sentinel-project"

    def _fake_download(project_path: Path, *_args, **_kwargs) -> None:
        project_path.mkdir(parents=True, exist_ok=True)

    class _DummyClient:
        def __init__(self, *_, **__):
            pass

        def close(self) -> None:  # pragma: no cover - noop stub
            pass

    class _DummyHTTPX:
        Client = _DummyClient

    monkeypatch.setattr(specify_cli, "httpx", _DummyHTTPX())
    monkeypatch.setattr(specify_cli, "download_and_extract_template", _fake_download)
    monkeypatch.setattr(specify_cli, "ensure_executable_scripts", lambda *_, **__: None)
    prompt_calls: list[str | None] = []

    def _record_prompts(_project_path: Path, assistant: str | None = None) -> int:
        prompt_calls.append(assistant)
        return 0

    monkeypatch.setattr(specify_cli, "sync_agent_prompt_bundles", _record_prompts)

    uv_calls: list[Path] = []
    monkeypatch.setattr(specify_cli, "run_uv_sync_in_project", lambda path: uv_calls.append(path))

    sentinel_calls: list[Path] = []
    monkeypatch.setattr(
        specify_cli,
        "run_sentinel_selfcheck_in_project",
        lambda path: sentinel_calls.append(path),
    )

    # ensure CLI skips git operations to keep the test hermetic
    result = runner.invoke(
        specify_cli.app,
        [
            "init",
            str(project_dir),
            "--ai",
            "codex",
            "--script",
            "sh",
            "--sentinel",
            "--ignore-agent-tools",
            "--no-git",
        ],
    )
    assert result.exit_code == 0, result.output
    assert uv_calls == [project_dir]
    assert sentinel_calls == [project_dir]
    assert (project_dir / ".sentinel" / "DECISIONS.md").exists()
    assert prompt_calls == ["codex"]

    payload = {
        "ok": True,
        "checks": [
            {"name": "capsule", "status": "pending", "duration": 0.0, "data": {"message": "todo"}},
            {"name": "mcp", "status": "pending", "duration": 0.0, "data": {"message": "missing"}},
        ],
    }

    invoked_roots: list[Path] = []

    def _fake_invoke(root_path: Path) -> tuple[int, dict, str]:
        invoked_roots.append(root_path)
        return 0, payload, ""

    monkeypatch.setattr(specify_cli, "_invoke_sentinel_selfcheck_json", _fake_invoke)

    check_result = runner.invoke(specify_cli.app, ["check", "--root", str(project_dir)])
    assert check_result.exit_code == 0, check_result.output
    assert invoked_roots == [project_dir]


def test_sentinel_project_package_can_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pytest.importorskip("hatchling")
    monkeypatch.setattr(specify_cli, "run_uv_sync_in_project", lambda *_: None)
    monkeypatch.setattr(specify_cli, "run_sentinel_selfcheck_in_project", lambda *_: None)

    (tmp_path / "README.md").write_text("sentinel-kit scaffold", encoding="utf-8")
    specify_cli.apply_sentinel_scaffold(tmp_path, tracker=None, assistant="codex")

    result = subprocess.run(
        [sys.executable, "-m", "hatchling", "build"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    wheel_files = list((tmp_path / "dist").glob("*.whl"))
    assert wheel_files, "expected hatchling build to produce a wheel"


def test_specify_check_succeeds_with_pending(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "ok": True,
        "checks": [
            {"name": "capsule", "status": "pending", "duration": 0.0, "data": {"message": "todo"}},
            {"name": "sentinels", "status": "ok", "duration": 0.1, "data": {"message": "ok"}},
        ],
    }

    monkeypatch.setattr(
        specify_cli,
        "_invoke_sentinel_selfcheck_json",
        lambda root: (0, payload, ""),
    )

    result = runner.invoke(specify_cli.app, ["check", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "pending checks" in result.stdout.lower()
    assert "capsule" in result.stdout
    assert "sentinels" in result.stdout


def test_specify_check_fails_on_failed_check(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "ok": False,
        "checks": [
            {"name": "sentinels", "status": "fail", "duration": 0.2, "error": {"message": "tests failed"}},
        ],
    }

    monkeypatch.setattr(
        specify_cli,
        "_invoke_sentinel_selfcheck_json",
        lambda root: (1, payload, "boom"),
    )

    result = runner.invoke(specify_cli.app, ["check", "--root", str(tmp_path)])
    assert result.exit_code == 1
    assert "failed" in result.output.lower()
    assert "tests failed" in result.stdout


def test_run_sentinel_selfcheck_returns_payload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "ok": True,
        "checks": [
            {"name": "capsule", "status": "pending", "duration": 0.0},
        ],
    }

    monkeypatch.setattr(
        specify_cli,
        "_invoke_sentinel_selfcheck_json",
        lambda root: (0, payload, ""),
    )

    result = specify_cli.run_sentinel_selfcheck(tmp_path)
    assert result is payload


def test_run_sentinel_selfcheck_raises_on_failed_checks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "ok": False,
        "checks": [
            {"name": "mcp", "status": "fail", "duration": 0.1, "error": {"message": "smoke failed"}},
        ],
    }

    monkeypatch.setattr(
        specify_cli,
        "_invoke_sentinel_selfcheck_json",
        lambda root: (0, payload, ""),
    )

    with pytest.raises(typer.Exit) as excinfo:
        specify_cli.run_sentinel_selfcheck(tmp_path)
    assert excinfo.value.exit_code == 1
