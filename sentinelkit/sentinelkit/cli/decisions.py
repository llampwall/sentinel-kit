"""Decision log CLI namespace."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from sentinelkit.utils.errors import SentinelKitError, serialize_error

from .decision_log import DecisionLedger, DecisionLedgerError, DecisionPayload
from .state import get_context

app = typer.Typer(help="Decision log utilities.")


@app.command("append", help="Append to the decision ledger.")
def append(
    ctx: typer.Context,
    author: Annotated[str, typer.Option("--author", "-a", help="Author or agent for the ledger entry.")],
    scope: Annotated[
        list[str],
        typer.Option(
            "--scope",
            "-s",
            help="Scope paths (repeat flag for multiple entries, e.g., --scope file1 --scope file2).",
        ),
    ],
    decision: Annotated[str, typer.Option("--decision", "-d", help="Decision summary text.")],
    rationale: Annotated[str, typer.Option("--rationale", "-r", help="Rationale for the decision.")],
    outputs: Annotated[
        list[str],
        typer.Option(
            "--output-path",
            "--outputs",
            "-o",
            help="Output artifacts touched by this decision (repeat flag for multiple entries).",
        ),
    ],
    supersedes: Annotated[
        str,
        typer.Option("--supersedes", help="Decision id that is superseded (defaults to 'none')."),
    ] = "none",
    decision_id: Annotated[
        str | None,
        typer.Option("--id", help="Explicit decision id (must match the ledger NEXT_ID)."),
    ] = None,
    date: Annotated[
        str | None,
        typer.Option("--date", help="Override the entry date (YYYY-MM-DD)."),
    ] = None,
    agent: Annotated[
        str | None,
        typer.Option("--agent", help="Agent name for ProducedBy header (defaults to author)."),
    ] = None,
    rules_hash: Annotated[
        str | None,
        typer.Option("--rules-hash", help="Rules hash for ProducedBy header (defaults to '<agent>@1.0')."),
    ] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview changes without writing the ledger.")] = False,
    preview: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-O",
            help="Optional preview file to write (useful for CI diffs); relative to --root when not absolute.",
        ),
    ] = None,
) -> None:
    """Append a structured decision entry."""
    context = get_context(ctx)
    ledger_path = context.root / ".sentinel" / "DECISIONS.md"
    preview_path = _resolve_optional_path(context.root, preview)
    payload = DecisionPayload(
        author=author,
        scope=_join_values(scope, "scope"),
        decision=decision,
        rationale=rationale,
        outputs=_require_values(outputs, "outputs"),
        supersedes=supersedes,
        date_override=date,
    )
    ledger = DecisionLedger(ledger_path)
    try:
        result = ledger.append(
            payload,
            agent=agent,
            rules_hash=rules_hash,
            dry_run=dry_run,
            output_path=preview_path,
            decision_id=decision_id,
        )
    except DecisionLedgerError as error:
        _emit_error(ctx, error)
    else:
        _emit_decision_result(ctx, result)


def _emit_decision_result(ctx: typer.Context, result) -> None:
    data = {
        "id": result.id,
        "ledger": str(result.ledger_path),
        "dry_run": result.dry_run,
        "wrote_ledger": result.wrote_ledger,
        "preview": str(result.output_path) if result.output_path else None,
        "snippets": asdict(result.snippets),
    }
    if ctx.obj.format == "json":
        typer.echo(json.dumps(data, indent=2))
    else:
        status = "previewed" if result.dry_run else "written"
        typer.echo(f"[sentinel] Decision {result.id} {status} in {result.ledger_path}")
        typer.echo("ProducedBy snippet:")
        typer.echo(f"  {result.snippets.plain}")


def _emit_error(ctx: typer.Context, error: SentinelKitError) -> None:
    payload = serialize_error(error)
    if ctx.obj.format == "json":
        typer.echo(json.dumps({"ok": False, "error": payload}, indent=2))
    else:
        typer.secho(f"Error: {payload.get('message')}", err=True, fg=typer.colors.RED)
    raise typer.Exit(1)


def _join_values(values: list[str], label: str) -> str:
    entries = _require_values(values, label)
    return ", ".join(entries)


def _require_values(values: list[str], label: str) -> list[str]:
    normalized = [value.strip() for value in values if value and value.strip()]
    if not normalized:
        raise typer.BadParameter(f"At least one --{label} value is required.")
    return normalized


def _resolve_optional_path(root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else (root / path)
