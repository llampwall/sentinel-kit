"""MCP helpers for SentinelKit."""

from __future__ import annotations

import typer

from ..state import get_context
from . import server

app = typer.Typer(help="SentinelKit MCP utilities (placeholder).")


@app.command("server", help="Launch the MCP stdio server.")
def launch(ctx: typer.Context) -> None:
    """Start the asyncio MCP server rooted at the provided repository path."""
    context = get_context(ctx)
    server.serve(root=context.root)


__all__ = ["app"]
