"""Context CLI namespace."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional, Tuple

import typer

from sentinelkit.context.lint import ContextLintError, LintSummary, lint_context
from sentinelkit.scripts.md_surgeon import MarkdownSurgeonError, SurgeonOptions, synchronize_snippet
from sentinelkit.utils.errors import build_error_payload, serialize_error

from .state import CLIContext, OutputFormat, get_context

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
    sync_docs: bool = typer.Option(
        False,
        "--sync-docs",
        help="Refresh README snippets from `.sentinel/snippets` after linting.",
    ),
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

    if sync_docs:
        try:
            _sync_capsule_docs(context)
        except ContextLintError as error:
            _render_error(error, context.format)
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


def _sync_capsule_docs(context: CLIContext) -> None:
    snippet = context.root / ".sentinel/snippets/capsules.md"
    readme = context.root / "README.md"
    if not snippet.exists():
        raise ContextLintError(
            build_error_payload(
                code="context.docs.missing_snippet",
                message=f"Snippet '{snippet}' does not exist.",
            )
        )
    if not readme.exists():
        raise ContextLintError(
            build_error_payload(
                code="context.docs.missing_readme",
                message=f"Documentation target '{readme}' does not exist.",
            )
        )
    try:
        synchronize_snippet(
            SurgeonOptions(
                file=readme,
                marker="SENTINEL:CAPSULES",
                content_path=snippet,
            )
        )
    except MarkdownSurgeonError as error:
        raise ContextLintError(error.payload) from error
    typer.echo("Synced README capsule snippet via md-surgeon.")
