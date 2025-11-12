"""MCP helpers for SentinelKit."""

from __future__ import annotations

import typer

from . import server

app = typer.Typer(help="SentinelKit MCP utilities (scaffold).")
app.command("server")(server.serve)

__all__ = ["app"]