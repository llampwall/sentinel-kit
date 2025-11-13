"""Capsule CLI namespace."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sentinelkit.capsule.generator import CapsuleGenerator, CapsuleGeneratorError
from sentinelkit.utils.errors import serialize_error

from .state import get_context

app = typer.Typer(help="Capsule generation helpers.")


@app.command("generate", help="Generate capsules from specs.")
def generate(
    ctx: typer.Context,
    spec: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=True, file_okay=False, help="Path to Spec-Kit feature directory."),
    ],
    decision: Annotated[str, typer.Option(..., help="Decision ID to embed in the capsule header.")],
    agent: Annotated[str, typer.Option("--agent", "-a", help="Agent name for ProducedBy header.")] = "ROUTER",
    rules_hash: Annotated[
        str | None,
        typer.Option("--rules-hash", help="Rules hash for ProducedBy header (defaults to '<agent>@1.0')."),
    ] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print capsule to stdout without writing file.")] = False,
) -> None:
    """Generate a capsule from the given spec directory."""
    context = get_context(ctx)
    generator = CapsuleGenerator(root=context.root)
    try:
        capsule_path = generator.generate(
            spec_dir=spec,
            decision=decision,
            agent=agent,
            rules_hash=rules_hash,
            write=not dry_run,
        )
    except CapsuleGeneratorError as error:
        payload = serialize_error(error)
        if context.format == "json":
            typer.echo({"ok": False, "error": payload})
        else:
            typer.secho(f"Capsule generation failed -> {payload['message']}", fg="red")
        raise typer.Exit(1)

    if dry_run:
        typer.echo(capsule_path.read_text(encoding="utf-8"))
    else:
        typer.secho(f"capsule:generate -> {capsule_path}", fg="green")
