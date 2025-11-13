# SentinelKit (Python Edition)

SentinelKit is the enforcement layer that keeps [Spec‑Kit](https://github.com/github/spec-kit) honest.  
Everything in this repo is implemented in Python and distributed via `uv`, so bootstrapping Sentinel on any platform is just a couple of commands.

> **Note:** SentinelKit bundles the Spec‑Kit workflow the project depends on—you don’t need to install the upstream repo separately. The message above is simply a nod to Spec‑Kit’s origins: `/speckit.*` still create the specs/plans/tasks, and SentinelKit layers the enforcement and CLI surfaced in this README.

---

## Table of Contents

1. [Why Sentinel?](#why-sentinel)
2. [Quick Start](#quick-start)
3. [CLI Overview](#cli-overview)
4. [Slash Command Gates](#slash-command-gates)
5. [MCP Workflow](#mcp-workflow)
6. [Tests & CI](#tests--ci)
7. [Repository Layout](#repository-layout)
8. [Support & Resources](#support--resources)

---

## Why Sentinel?

Specs are executable contracts. SentinelKit makes sure we live up to them by enforcing:

- **Contracts** – deterministic validation of every fixture against its schema.
- **Context** – Allowed Context linting, capsule line budgets, and prompt scaffolding.
- **Sentinel Tests** – pytest suites encoding historical regressions.
- **Provenance** – decision ledger + runbook CLIs with ProducedBy snippets.
- **MCP Surfaces** – a JSON‑RPC stdio server exposing the same gates to editors and agents.

All of this runs on Python 3.12 via `uv`. Node tooling (pnpm, vitest, tsconfig) has been removed entirely.

---

## Quick Start

```bash
# 1) Install the Specify CLI (with Sentinel scaffolding built-in)
uv tool install --from git+https://github.com/llampwall/sentinel-kit.git specify

# 2) Scaffold a project with Sentinel assets + bootstrap
uvx specify init <project> --sentinel

# 3) From any Sentinel repo, validate all gates
uv run sentinel --format pretty selfcheck
```

> **Tip:** `selfcheck` runs contracts, context lint, capsule dry-run, sentinel tests, MCP smoke, decision/runbook hooks, etc. Keep the JSON output around for CI:
> ```bash
> uv run sentinel --format json selfcheck > .artifacts/selfcheck.json
> ```

---

## CLI Overview

All commands are exposed via `uv run sentinel ...`. Use `--format json` for machine-readable output.

| Command | Description |
| --- | --- |
| `sentinel capsule generate <spec-dir> [--dry-run]` | Renders capsules with ProducedBy headers, Allowed Context, and line-budget enforcement. |
| `sentinel prompts render --mode {router,capsule}` | Validates capsules, renders router/agent prompts, writes router logs. |
| `sentinel decisions append ...` | Appends structured entries to `.sentinel/DECISIONS.md` with portalocker-based locking and ProducedBy snippets. |
| `sentinel runbook append ...` | Appends notes to `.sentinel/docs/IMPLEMENTATION.md` using the structured runbook updater. |
| `sentinel context lint [--capsule ...]` | Runs the Allowed Context linter with artifact budgets/overrides. |
| `sentinel contracts validate [--id ... | --path ...]` | Validates fixtures against versioned schemas. |
| `sentinel sentinels run [--json-report ... --junit ...]` | Executes the sentinel pytest suites. |
| `sentinel mcp server` | Async JSON‑RPC stdio server exposing contract/context/tests/ledger tools. |
| `sentinel mcp smoke [--format json]` | End‑to‑end smoke runner that spawns the server, drives initialize/list/call, and reports failures with Rich panels. |
| `sentinel snippets sync [--marker ...]` | Syncs README/UPSTREAM snippets (capsules, MCP badge, workflow badge, etc.) via the Python md‑surgeon. |
| `sentinel agents roster [--format json]` | Lists router/agent metadata sourced from `.sentinel/agents/**`. |

All commands honor `--root <path>` to run against another repo.

---

## Slash Command Gates

The `/speckit.*` templates now call `scripts/bash/run-sentinel-gate.sh` (or `scripts/powershell/run-sentinel-gate.ps1`) after their prerequisite scripts. Each gate:

1. Reads prereq output (feature dir, spec paths, repo root) from a temp JSON file.
2. Runs the relevant Sentinel CLIs (`sentinel contracts validate`, `sentinel context lint`, capsule dry-run, `sentinel sentinels run`).
3. Fails fast with Rich output if any gate breaks.

Gates covered:
- `constitution` – contracts + context
- `specify` – contracts + context + capsule
- `plan/tasks/clarify/analyze/checklist` – contracts + context
- `implement` – contracts + context + capsule + sentinel tests

Environment overrides:
- `SENTINEL_GATE_UV` forces a specific `uv` binary (used in CI stub tests).
- `WSLENV` is extended automatically so WSL paths resolve properly.

---

## MCP Workflow

1. **Server** – Start the stdio server in a repo:
   ```bash
   uvx sentinel mcp server
   ```

2. **Smoke** – Validate the handshake (initialize → list → call):
   ```bash
   uvx sentinel mcp smoke --timeout-call 90
   ```

3. **.mcp.json entry**
   ```json
   {
     "mcpServers": {
       "sentinel": {
         "command": "uvx",
         "args": ["sentinel", "mcp", "server"],
         "env": { "PYTHONUTF8": "1" }
       }
     }
   }
   ```

The smoke runner is wired into `sentinel selfcheck` and the CI workflow. Dry-run decision previews are cleaned up automatically.

---

## Tests & CI

- **Bootstrap:** `uv sync --locked --dev` (with fallbacks), `uv run sentinel selfcheck`, `uv run pytest -q`.
- **Sentinel suites:** `uv run sentinel sentinels run --json-report test-results/sentinels.json --junit test-results/sentinels.xml`.
- **MCP smoke:** `uv run python -m sentinelkit.cli.main mcp smoke --format json`.
- **Check for banned Node artifacts:** `uv run python scripts/check_node_artifacts.py`.
- **CI (`.github/workflows/sentinel-ci.yml`)** runs all of the above on Ubuntu/macOS/Windows, uploads artifacts, and fails fast on any regression.

Run these locally before opening a PR to get the same signal the workflow enforces.

---

## Repository Layout

```
sentinelkit/            # Python package (CLI, MCP server, contracts/context/capsule modules, tests)
.sentinel/              # Shipped assets (agents, context limits, contracts, prompts, snippets, templates)
scripts/                # Bootstrap helpers, slash-command gate scripts, node-artifact guard
tests/                  # Pytest suites (sentinel regressions, MCP server/smoke, CLI integration)
docs/                   # Contributor docs (quickstart, support)
```

Key documents:
- `.sentinel/docs/sentinel_asset_mapping.md` – canonical list of assets copied by `specify init --sentinel`.
- `.sentinel/docs/IMPLEMENTATION.template.md` – runbook seed used in new scaffolds.
- `.sentinel/docs/IMPLEMENTATION.md` – live runbook (kept in repo for provenance, optional to ship to end users).

---

## Support & Resources

- [docs/quickstart.md](docs/quickstart.md) – uv-based bootstrap instructions.
- [SUPPORT.md](SUPPORT.md) – sync/selfcheck/test workflow before filing issues.
- [.specify/README.md](.specify/README.md) – agent-facing instructions embedded in Spec-Kit scaffolds.
- [Spec‑Kit docs](https://github.com/github/spec-kit#readme) – the upstream spec rails that SentinelKit enforces. Always start there for `/speckit.*` behaviors, then layer Sentinel gates on top.
- `.sentinel/snippets/*` – reusable snippets for README badges, MCP guidance, capsules, etc.

If you find issues or have feature requests, open an issue or pull request on GitHub—just make sure `uv run sentinel selfcheck` is green first.

---

Happy shipping! The whole point of SentinelKit is to give you deterministic guards so your specs stay true across repos, operating systems, and agents. If `selfcheck` passes, you’re good to merge. !*** End Patch
