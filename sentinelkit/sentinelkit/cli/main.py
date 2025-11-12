"""Typer application entry point for SentinelKit."""

from __future__ import annotations

import typer

from sentinelkit import capsule, contracts, context, prompt, scripts, utils  # noqa: F401

from . import contract_validate, context_lint, decision_log, mcp, selfcheck

app = typer.Typer(help="SentinelKit CLI (scaffold)")

app.command("contracts", help="Validate Sentinel contracts.")(contract_validate.run)
app.command("context", help="Lint allowed context.")(context_lint.run)
app.command("decisions", help="Append to the decision log.")(decision_log.run)
app.command("selfcheck", help="Run SentinelKit diagnostics.")(selfcheck.run)
app.add_typer(mcp.app, name="mcp")


def main() -> None:  # pragma: no cover - Typer handles invocation
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
