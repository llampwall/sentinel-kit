"""Shared CLI context helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import typer

OutputFormat = Literal["pretty", "json"]


@dataclass(slots=True)
class CLIContext:
    root: Path
    format: OutputFormat


def set_context(ctx: typer.Context, *, root: Path, output: OutputFormat) -> None:
    ctx.obj = CLIContext(root=root, format=output)


def get_context(ctx: typer.Context) -> CLIContext:
    if ctx.obj is None:
        raise typer.BadParameter("Missing CLI context; the root callback did not initialize state.")
    return ctx.obj
