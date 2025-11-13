"""Contracts CLI namespace."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from sentinelkit.contracts.api import ContractValidator
from sentinelkit.contracts.loader import ContractLoader

from .state import get_context

app = typer.Typer(help="Contracts tooling.")


@app.command("validate", help="Validate Sentinel contracts.")
def validate(
    ctx: typer.Context,
    contract_id: Annotated[
        str | None,
        typer.Option("--id", "--contract", help="Validate only the specified contract id."),
    ] = None,
    fixture_path: Annotated[
        Path | None,
        typer.Option("--path", help="Validate a specific fixture path."),
    ] = None,
) -> None:
    """Validate contracts against fixtures."""
    context = get_context(ctx)
    loader = ContractLoader(root=context.root)
    validator = ContractValidator(loader)
    normalized_path = (
        (context.root / fixture_path).resolve() if fixture_path and not fixture_path.is_absolute() else fixture_path
    )
    results = validator.validate_all(
        contract_id=contract_id,
        fixture_path=normalized_path,
    )
    ok = all(result.ok for result in results)
    console = Console()

    if context.format == "json":
        payload = {"ok": ok, "results": [result.to_dict() for result in results]}
        typer.echo(json.dumps(payload, indent=2))
    else:
        table = Table(title="Contract validation")
        table.add_column("Contract")
        table.add_column("Fixture")
        table.add_column("Status")
        table.add_column("Errors")
        for result in results:
            errors = "\n".join(error.message for error in result.errors) or "-"
            status = "✅" if result.ok else "❌"
            table.add_row(result.contract, result.fixture.name, status, errors)
        console.print(table)
        console.print("[bold green]All contracts valid.[/bold green]" if ok else "[bold red]Validation failed.[/bold red]")

    if not ok:
        raise typer.Exit(1)
