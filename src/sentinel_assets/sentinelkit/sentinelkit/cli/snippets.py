"""Snippets CLI namespace."""

from __future__ import annotations

from typing import Optional

import typer

from sentinelkit.scripts.snippets import SnippetSyncError, sync_snippets
from sentinelkit.utils.errors import serialize_error

from .state import get_context

app = typer.Typer(help="Snippet synchronization helpers.")


@app.command("sync", help="Synchronize documentation snippets.")
def sync(
    ctx: typer.Context,
    marker: Optional[str] = typer.Option(
        None,
        "--marker",
        "-m",
        help="Comma-separated markers to sync (defaults to all).",
        show_default=False,
    ),
) -> None:
    context = get_context(ctx)
    markers = [m.strip() for m in marker.split(",")] if marker else None
    try:
        updated = sync_snippets(root=context.root, markers=markers)
    except SnippetSyncError as error:
        payload = serialize_error(error)
        if context.format == "json":
            typer.echo({"ok": False, "error": payload})
        else:
            typer.secho(f"Snippet sync failed -> {payload['message']}", fg="red")
        raise typer.Exit(1)

    if context.format == "json":
        typer.echo({"ok": True, "updated": [str(path) for path in updated]})
    else:
        for path in updated:
            typer.secho(f"synced snippet -> {path}", fg="green")
