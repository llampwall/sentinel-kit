"""Shared CLI context helpers."""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import typer

OutputFormat = Literal["pretty", "json"]


@dataclass(slots=True)
class EnvironmentInfo:
    is_ci: bool
    platform: str
    python_version: str


@dataclass(slots=True)
class CLIContext:
    root: Path
    format: OutputFormat
    env: EnvironmentInfo


def set_context(ctx: typer.Context, *, root: Path, output: OutputFormat) -> None:
    ctx.obj = CLIContext(root=root, format=output, env=_detect_environment())


def get_context(ctx: typer.Context) -> CLIContext:
    if ctx.obj is None:
        raise typer.BadParameter("Missing CLI context; the root callback did not initialize state.")
    return ctx.obj


def _detect_environment() -> EnvironmentInfo:
    return EnvironmentInfo(
        is_ci=os.getenv("CI", "").lower() == "true",
        platform=platform.platform(),
        python_version=platform.python_version(),
    )
