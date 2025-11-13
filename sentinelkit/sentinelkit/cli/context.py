"""Context CLI namespace."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional, Tuple

import typer

from sentinelkit.context.lint import ContextLintError, LintSummary, lint_context
from sentinelkit.utils.errors import serialize_error

from .state import OutputFormat, get_context

app = typer.Typer(help="Context linting and utilities.")


@app.command("lint", help="Run the allowed-context linter.")
def lint(
    ctx: typer.Context,
    capsule: Annotated[
        Tuple[Path, ...],
        typer.Option(
            "--capsule",
            "-c",
            help="Only lint the specified capsule path (repeat as needed).",
            show_default=False,
            exists=False,
            dir_okay=False,
            file_okay=True,
        ),
    ] = (),
    strict: bool = typer.Option(False, "--strict", help="Treat warnings as errors."),
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            help="Override the default context limits configuration.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            show_default=False,
        ),
    ] = None,
    schema: Annotated[
        Optional[Path],
        typer.Option(
            "--schema",
            help="Override the context limits JSON schema path.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            show_default=False,
        ),
    ] = None,
) -> None:
    """Run the context linter."""
    context = get_context(ctx)
    try:
        summary = lint_context(
            capsules=capsule,
            strict=strict,
            root=context.root,
            config_path=config,
            schema_path=schema,
        )
    except ContextLintError as error:
        _render_error(error, context.format)
        raise typer.Exit(1)

    _render_summary(summary, context.format)
    if summary.should_fail():
        raise typer.Exit(1)


def _render_summary(summary: LintSummary, output: OutputFormat) -> None:
    if output == "json":
        typer.echo(summary.to_json(indent=2))
        return

    if not summary.diagnostics:
        typer.secho(
            f"context lint OK scanned {summary.checked_files} file(s)",
            fg="green",
        )
        return

    for diag in summary.diagnostics:
        prefix = "X" if diag.severity == "error" else "!"
        typer.echo(f"{prefix} [{diag.code}] {diag.path} -> {diag.message}")
    typer.echo(
        f"context lint summary: {summary.errors} error(s), {summary.warnings} warning(s)"
    )


def _render_error(error: ContextLintError, output: OutputFormat) -> None:
    payload = serialize_error(error)
    if output == "json":
        typer.echo(json.dumps({"ok": False, "error": payload}, indent=2))
        return
    message = payload["message"]
    typer.secho(f"context lint failed -> {message}", fg="red")
    remediation = payload.get("remediation")
    if remediation:
        typer.echo(f"Hint: {remediation}")
