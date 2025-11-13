"""Sentinel regression CLI namespace."""

from __future__ import annotations

import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Annotated, Optional

import pytest
import typer

from .state import get_context

app = typer.Typer(help="Sentinel regression helpers.")


def run_sentinel_pytest(
    *,
    root: Path,
    marker: str | None = None,
    junit: Path | None = None,
    json_report: Path | None = None,
    quiet: bool = False,
) -> tuple[int, dict]:
    """Execute sentinel pytest suites and return (exit_code, summary)."""

    args: list[str] = ["-q", "tests/sentinels"]
    if marker:
        args.extend(["-m", marker])
    if junit:
        junit.parent.mkdir(parents=True, exist_ok=True)
        args.append(f"--junitxml={junit}")

    cwd = Path.cwd()
    try:
        os.chdir(root)
        if quiet:
            buffer = io.StringIO()
            with redirect_stdout(buffer), redirect_stderr(buffer):
                exit_code = pytest.main(args)
        else:
            exit_code = pytest.main(args)
    finally:
        os.chdir(cwd)

    summary = {"ok": exit_code == 0, "root": str(root), "args": args}
    if json_report:
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if not quiet:
        typer.echo(json.dumps(summary, indent=2))
    return exit_code, summary


@app.command("run", help="Run sentinel pytest suites.")
def run(
    ctx: typer.Context,
    marker: Annotated[
        Optional[str],
        typer.Option("--marker", "-m", help="Pytest marker expression to filter sentinel tests.", show_default=False),
    ] = None,
    junit: Annotated[
        Optional[Path],
        typer.Option(
            "--junit",
            help="Optional path to write JUnit XML results.",
            show_default=False,
            writable=True,
        ),
    ] = None,
    json_report: Annotated[
        Optional[Path],
        typer.Option(
            "--json-report",
            help="Optional path to write JSON summary.",
            show_default=False,
            writable=True,
        ),
    ] = None,
) -> None:
    """Execute sentinel pytest suites and surface exit status + optional reports."""

    context = get_context(ctx)
    exit_code, _summary = run_sentinel_pytest(
        root=context.root,
        marker=marker,
        junit=junit,
        json_report=json_report,
        quiet=json_report is not None,
    )
    if exit_code != 0:
        raise typer.Exit(exit_code)
