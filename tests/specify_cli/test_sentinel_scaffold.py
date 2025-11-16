"""Tests for Sentinel asset scaffolding inside specify init."""

from __future__ import annotations

from pathlib import Path
import importlib
import subprocess
import sys
import tomllib

import pytest
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

    specify_cli.apply_sentinel_scaffold(tmp_path, tracker=None)

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
    project_dir = tmp_path / "mobile-comfy"

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
    monkeypatch.setattr(specify_cli, "sync_agent_prompt_bundles", lambda *_: 0)

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

    check_calls: list[Path | None] = []
    monkeypatch.setattr(
        specify_cli,
        "run_sentinel_selfcheck",
        lambda root=None: check_calls.append(root),
    )

    check_result = runner.invoke(specify_cli.app, ["check", "--root", str(project_dir)])
    assert check_result.exit_code == 0, check_result.output
    assert check_calls == [project_dir]


def test_sentinel_project_package_can_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pytest.importorskip("hatchling")
    monkeypatch.setattr(specify_cli, "run_uv_sync_in_project", lambda *_: None)
    monkeypatch.setattr(specify_cli, "run_sentinel_selfcheck_in_project", lambda *_: None)

    (tmp_path / "README.md").write_text("sentinel-kit scaffold", encoding="utf-8")
    specify_cli.apply_sentinel_scaffold(tmp_path, tracker=None)

    result = subprocess.run(
        [sys.executable, "-m", "hatchling", "build", "--wheel"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
