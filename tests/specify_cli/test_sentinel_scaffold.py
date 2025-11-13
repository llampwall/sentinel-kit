"""Tests for Sentinel asset scaffolding inside specify init."""

from __future__ import annotations

from pathlib import Path
import importlib

import pytest

specify_cli = importlib.import_module("specify_cli.__init__")


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
    assert (tmp_path / ".tool-versions").exists()
    assert (tmp_path / "scripts" / "bootstrap.py").exists()
    assert (tmp_path / "sentinelkit" / "pyproject.toml").exists()
    assert (tmp_path / ".sentinel" / "docs" / "IMPLEMENTATION.md").exists()
    assert (tmp_path / ".github" / "workflows" / "sentinel-ci.yml").exists()
    assert ("uv", tmp_path) in calls
    assert ("selfcheck", tmp_path) in calls
