"""Typer application entry point for SentinelKit."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sentinelkit import capsule as _capsule_pkg  # noqa: F401
from sentinelkit import contracts as _contracts_pkg  # noqa: F401
from sentinelkit import context as _context_pkg  # noqa: F401
from sentinelkit import prompt as _prompt_pkg  # noqa: F401
from sentinelkit import scripts as _scripts_pkg  # noqa: F401
from sentinelkit import utils as _utils_pkg  # noqa: F401

from . import capsule, context, contracts, decisions, mcp, prompts, runbook, selfcheck, sentinels, snippets
from .state import OutputFormat, set_context

app = typer.Typer(help="SentinelKit CLI (scaffold)")


@app.callback()
def root_callback(
    ctx: typer.Context,
    root: Annotated[
        Path,
        typer.Option(
            dir_okay=True,
            file_okay=False,
            exists=True,
            help="Repository root path for SentinelKit operations.",
        ),
    ] = Path("."),
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            case_sensitive=False,
            help="Output format for commands that support structured results.",
        ),
    ] = "pretty",
) -> None:
    """Initialize the CLI context shared by subcommands."""
    set_context(ctx, root=root.resolve(), output=output_format)


app.command("selfcheck", help="Run SentinelKit diagnostics.")(selfcheck.run)
app.add_typer(contracts.app, name="contracts")
app.add_typer(context.app, name="context")
app.add_typer(capsule.app, name="capsule")
app.add_typer(prompts.app, name="prompts")
app.add_typer(sentinels.app, name="sentinels")
app.add_typer(decisions.app, name="decisions")
app.add_typer(runbook.app, name="runbook")
app.add_typer(mcp.app, name="mcp")
app.add_typer(snippets.app, name="snippets")


def main() -> None:  # pragma: no cover - Typer handles invocation
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
