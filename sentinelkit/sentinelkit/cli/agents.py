"""Agent roster CLI namespace."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.table import Table

from sentinelkit.prompt.agents import AgentRegistryError, load_agents
from sentinelkit.utils.errors import serialize_error

from .state import get_context

app = typer.Typer(help="Agent roster helpers.")


@app.command("roster", help="Print the Sentinel agent roster.")
def roster(
    ctx: typer.Context,
    include_body: Annotated[
        bool,
        typer.Option(
            "--include-body",
            help="Include ROLE/PLAYBOOK text in JSON output (pretty mode always omits body).",
        ),
    ] = False,
) -> None:
    """Emit agent metadata for routers/CapsuleAuthor workflows."""
    context = get_context(ctx)
    try:
        registry = load_agents(root=context.root)
    except AgentRegistryError as error:
        payload = serialize_error(error)
        if context.format == "json":
            typer.echo(json.dumps({"ok": False, "error": payload}, indent=2))
        else:
            typer.secho(f"agents roster failed -> {payload['message']}", fg="red")
        raise typer.Exit(1)

    agents_payload = [
        {
            "id": agent.id,
            "name": agent.name,
            "rulesHash": agent.rules_hash,
            "summary": agent.summary,
            "routingKeywords": agent.routing_keywords,
            "mountPaths": agent.mount_paths,
            "role": agent.role if include_body or context.format != "json" else None,
            "playbook": agent.playbook if include_body or context.format != "json" else None,
        }
        for agent in registry.agents
    ]

    if context.format == "json":
        for agent in agents_payload:
            if agent["role"] is None:
                agent["role"] = "(elided)"
            if agent["playbook"] is None:
                agent["playbook"] = "(elided)"
        typer.echo(json.dumps({"ok": True, "agents": agents_payload}, indent=2))
        return

    table = Table(title="Sentinel Agents", show_lines=False)
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Summary")
    table.add_column("Mount Paths")
    for agent in registry.agents:
        mounts = "\n".join(agent.mount_paths) or "-"
        table.add_row(agent.id, agent.name, agent.summary, mounts)
    typer.echo(table)
