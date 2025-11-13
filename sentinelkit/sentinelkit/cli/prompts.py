"""Prompts CLI namespace."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sentinelkit.prompt import PromptRenderer, PromptRenderingError
from sentinelkit.utils.errors import build_error_payload, serialize_error

from .state import get_context

app = typer.Typer(help="Prompt rendering utilities.")


@app.command("render", help="Render Sentinel prompts.")
def render(
    ctx: typer.Context,
    mode: Annotated[str, typer.Option("--mode", "-m", help="Prompt mode: router or capsule.")],
    capsule: Annotated[
        Path,
        typer.Option(
            "--capsule",
            "-c",
            exists=True,
            dir_okay=False,
            help="Path to capsule.md file.",
        ),
    ],
    agent: Annotated[
        str | None,
        typer.Option("--agent", "-a", help="Agent id (required for capsule mode)."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Optional file to write prompt output."),
    ] = None,
    router_json: Annotated[
        Path | None,
        typer.Option("--router-json", help="Router JSON payload to validate and log."),
    ] = None,
) -> None:
    """Render router or capsule prompts via the Python renderer."""
    context = get_context(ctx)
    renderer = PromptRenderer(root=context.root)
    mode = mode.lower()
    try:
        if mode == "router":
            prompt = renderer.render_router_prompt(capsule)
            _write_output(prompt, output)
            if router_json:
                log_path = renderer.write_router_log(capsule, router_json)
                typer.secho(f"router log -> {log_path}", fg="cyan")
            return
        if mode != "capsule":
            raise PromptRenderingError(
                build_error_payload(code="prompts.invalid_mode", message="Mode must be 'router' or 'capsule'.")
            )
        if not agent:
            raise PromptRenderingError(
                build_error_payload(
                    code="prompts.agent_required",
                    message="--agent is required when rendering capsule prompts.",
                )
            )
        prompt = renderer.render_agent_prompt(capsule, agent)
        _write_output(prompt, output)
    except PromptRenderingError as error:
        payload = serialize_error(error)
        if context.format == "json":
            typer.echo(json.dumps({"ok": False, "error": payload}, indent=2))
        else:
            typer.secho(f"Prompt rendering failed -> {payload['message']}", fg="red")
        raise typer.Exit(1)


def _write_output(content: str, destination: Path | None) -> None:
    if destination:
        destination.write_text(content, encoding="utf-8")
        typer.secho(f"wrote prompt -> {destination}", fg="green")
    else:
        typer.echo(content)
