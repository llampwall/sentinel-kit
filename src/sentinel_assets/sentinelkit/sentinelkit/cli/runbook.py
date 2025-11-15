"""Runbook CLI namespace."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from sentinelkit.runbook import RunbookUpdater
from sentinelkit.runbook.updater import RunbookUpdaterError
from sentinelkit.utils.errors import SentinelKitError, serialize_error

from .state import get_context

app = typer.Typer(help="Runbook helpers.")


@app.command("append", help="Append a note to IMPLEMENTATION.md.")
def append(
    ctx: typer.Context,
    section: Annotated[str, typer.Option("--section", "-s", case_sensitive=False, help="Runbook section slug.")],
    note: Annotated[str, typer.Option("--note", "-n", help="Runbook note to append.")],
    author: Annotated[str, typer.Option("--author", "-a", help="Person or agent authoring the note.")],
    timestamp: Annotated[
        str | None,
        typer.Option("--timestamp", help="Optional timestamp override (ISO8601, e.g., 2025-11-13T12:00Z)."),
    ] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview changes without writing the runbook.")] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-O", help="Optional preview file (relative to --root when not absolute)."),
    ] = None,
) -> None:
    """Append a structured runbook entry."""
    context = get_context(ctx)
    updater = RunbookUpdater(context.root / ".sentinel" / "docs" / "IMPLEMENTATION.md")
    preview_path = _resolve_optional_path(context.root, output)
    try:
        result = updater.append(
            section=section,
            note=note,
            author=author,
            timestamp=_parse_timestamp(timestamp),
            dry_run=dry_run,
            output_path=preview_path,
        )
    except RunbookUpdaterError as error:
        _emit_error(ctx, error)
    else:
        _emit_runbook_result(ctx, result)


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise typer.BadParameter("Timestamp must be ISO8601 (e.g., 2025-11-13T12:00Z).") from exc


def _resolve_optional_path(root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else (root / path)


def _emit_runbook_result(ctx: typer.Context, result) -> None:
    payload = {
        "section": result.section.slug,
        "path": str(result.path),
        "timestamp": result.timestamp,
        "dry_run": result.dry_run,
        "wrote_file": result.wrote_file,
        "preview": str(result.output_path) if result.output_path else None,
    }
    if ctx.obj.format == "json":
        typer.echo(json.dumps(payload, indent=2))
    else:
        status = "previewed" if result.dry_run else "updated"
        typer.echo(f"[sentinel] Runbook {status} ({result.section.title}) -> {result.path}")


def _emit_error(ctx: typer.Context, error: SentinelKitError) -> None:
    payload = serialize_error(error)
    if ctx.obj.format == "json":
        typer.echo(json.dumps({"ok": False, "error": payload}, indent=2))
    else:
        typer.secho(f"Error: {payload.get('message')}", err=True, fg=typer.colors.RED)
    raise typer.Exit(1)
