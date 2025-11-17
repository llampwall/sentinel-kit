"""Tests for the run-sentinel-gate helper scripts."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import List

import pytest

# These tests exercise the bash-based sentinel gate wrapper.
# On Windows, they end up going through WSL + pyenv-win shims and explode.
# The gate is only expected to run in a POSIX CI environment, so we skip here.
if os.name == "nt":
    pytest.skip(
        "Sentinel gate bash wrapper tests are POSIX-only; "
        "skip on Windows.",
        allow_module_level=True,
    )


@lru_cache()
def _bash_mode() -> str:
    if not shutil.which("bash"):
        pytest.skip("bash is not available on this system")
    try:
        result = subprocess.run(
            ["bash", "-c", "pwd"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        pytest.skip("unable to run bash for sentinel gate tests")
    path = result.stdout.strip()
    if path.startswith("/mnt/"):
        return "wsl"
    return "msys"


def _write_uv_stub(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    uv_path = bin_dir / "uv"
    uv_path.write_text(
        f"#!/usr/bin/env bash\n"
        'echo "[uv-stub] $@"\n'
        "exit 0\n",
        encoding="utf-8",
        newline="\n",
    )
    uv_path.chmod(uv_path.stat().st_mode | stat.S_IEXEC)


def _write_paths_json(path: Path, repo_root: Path, feature_dir: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "REPO_ROOT": _to_bash_path(repo_root),
                "FEATURE_DIR": _to_bash_path(feature_dir),
                "SPEC_FILE": _to_bash_path(feature_dir / "spec.md"),
                "IMPL_PLAN": _to_bash_path(feature_dir / "plan.md"),
            }
        ),
        encoding="utf-8",
    )


def _to_bash_path(path: Path) -> str:
    resolved = path.resolve()
    posix = resolved.as_posix()
    if len(posix) >= 3 and posix[1] == ":" and posix[2] == "/":
        drive = posix[0].lower()
        rest = posix[3:].lstrip("/")
        mode = _bash_mode()
        if mode == "wsl":
            return f"/mnt/{drive}/{rest}"
        return f"/{drive}/{rest}"
    return posix


def _run_gate(tmp_path: Path, gate: str) -> list[str]:
    repo_root = tmp_path / "repo"
    feature_dir = repo_root / "specs" / "123-feature"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "spec.md").write_text("# spec", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# plan", encoding="utf-8")
    paths_json = tmp_path / "paths.json"
    _write_paths_json(paths_json, repo_root, feature_dir)

    bin_dir = tmp_path / "bin"
    _write_uv_stub(bin_dir)

    env = os.environ.copy()
    env["PATH"] = ":".join([_to_bash_path(bin_dir), env.get("PATH", "")])
    env["SENTINEL_GATE_UV"] = _to_bash_path(bin_dir / "uv")
    current_wslenv = env.get("WSLENV", "")
    wslenv_entries = [entry for entry in current_wslenv.split(":") if entry]
    if "SENTINEL_GATE_UV/u" not in wslenv_entries:
        wslenv_entries.append("SENTINEL_GATE_UV/u")
    env["WSLENV"] = ":".join(wslenv_entries)

    paths_arg = _to_bash_path(paths_json)
    result = subprocess.run(
        ["bash", _to_bash_path(Path("scripts/bash/run-sentinel-gate.sh")), "--gate", gate, "--paths-json", paths_arg],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_run_sentinel_gate_specify(tmp_path: Path) -> None:
    logs = _run_gate(tmp_path, "specify")
    sentinel_lines = [line for line in logs if line.startswith("[sentinel-gate]")]
    assert any("contracts validate" in line for line in sentinel_lines)
    assert any("context lint" in line for line in sentinel_lines)
    assert any("capsule generate" in line for line in sentinel_lines)
    assert "[sentinel-gate] Gate 'specify' completed successfully." in sentinel_lines[-1]


def test_run_sentinel_gate_implement(tmp_path: Path) -> None:
    logs = _run_gate(tmp_path, "implement")
    sentinel_lines = [line for line in logs if line.startswith("[sentinel-gate]")]
    assert any("sentinel tests" in line for line in sentinel_lines)
    assert "[sentinel-gate] Gate 'implement' completed successfully." in sentinel_lines[-1]
