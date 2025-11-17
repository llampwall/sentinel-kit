# Testing Guide

This document captures how to validate SentinelKit and the Specify CLI whenever you change enforcement logic or the scaffold.

## Sentinel selfcheck semantics

- `uv run sentinel selfcheck` executes all enforcement gates (contracts, context, capsule, sentinel pytest suites, MCP smoke) concurrently.
- Every check reports a structured `status`:
  - `ok` — the guardrail ran and passed.
  - `pending` — the guardrail has not been configured yet (fresh scaffolds ship this way) but it is not considered a failure.
  - `fail` — the guardrail ran and reported an error; selfcheck exits with a non‑zero code.
- `--format json` emits machine-readable output. `specify check` consumes the same payload and should always treat `pending` checks as informational rather than a blocker.

## Smoke commands

Run these when iterating on SentinelKit itself or when validating a freshly scaffolded repository:

```bash
# Human-readable output with a summary table
uv run sentinel selfcheck --verbose

# Machine-readable output (preferred for CI and for specify check)
uv run sentinel --format json selfcheck

# Specify CLI gate (wraps the JSON selfcheck and renders results with pending/ok/fail badges)
specify check
```

A brand-new project is expected to show every gate as `pending` until you add real MCP configs or sentinel pytest suites. Both `sentinel selfcheck` and `specify check` still exit with code `0` in that state.

## Targeted pytest suites

Run these focused suites whenever you touch the sentinel CLI, the Specify CLI integration, or the vendored asset mirror:

```bash
# Specify CLI scaffold + check integration
uv run pytest tests/specify_cli/test_sentinel_scaffold.py -q

# Sentinel CLI (workspace copy) status/JSON semantics
uv run pytest tests/cli/test_selfcheck.py -q

# SentinelKit package selfcheck regressions
uv run pytest sentinelkit/tests/test_cli_selfcheck.py -q

# Vendored sentinel assets used by scaffolds
uv run pytest tests/sentinelkit/tests/test_cli_selfcheck_assets.py -q
```

## Full suite

Before sending a PR (or after invasive refactors) run the full suite to exercise every contract, scaffold, and test helper:

```bash
uv run pytest -q
```

This command is cross-platform. On Windows you can invoke it from PowerShell; on Linux/macOS the same arguments work in Bash.

## Coverage summary

| Area | Coverage |
| --- | --- |
| Sentinel CLI status semantics | `tests/cli/test_selfcheck.py`, `sentinelkit/tests/test_cli_selfcheck.py` |
| Specify CLI scaffold + pending/fail handling | `tests/specify_cli/test_sentinel_scaffold.py` |
| Vendored sentinel assets (what new scaffolds receive) | `tests/sentinelkit/tests/test_cli_selfcheck_assets.py` |
| End-to-end run of every remaining test (contracts, MCP, etc.) | `uv run pytest -q` |

These suites ensure that:

- JSON payloads always include `environment` metadata plus the per-check `status`.
- `specify check` surfaces `pending` rows without failing the gate.
- Any regression in the vendored `sentinel_assets` copy fails fast before release.

## Platform tips

- `uv` must be on your `PATH`. On Windows, run the commands from PowerShell where `uv.exe` is available (e.g., installed via `cargo-binstall` or `pipx`). On Linux/macOS, the Bash snippets above work as-is.
- The CLI emits JSON only when `--format json` is provided. Avoid scraping ANSI tables in automated tests; rely on the structured payload instead.
- If you edit sentinel tests or assets, re-run at least the targeted suites plus the full run to catch drift between the workspace copy and the vendored scaffold copy.
