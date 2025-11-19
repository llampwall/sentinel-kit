# Sentinel-Kit

Sentinel-Kit is the enforcement layer that keeps [Spec‑Kit](https://github.com/github/spec-kit) honest.  
Everything in this repo is implemented in Python and distributed via `uv`, so bootstrapping Sentinel on any platform is just a couple of commands.

> **Note:** Sentinel-Kit bundles the Spec‑Kit workflow the project depends on—you don’t need to install the upstream repo separately. The message above is simply a nod to Spec‑Kit’s origins: `/speckit.*` still create the specs/plans/tasks, and Sentinel-Kit layers the enforcement and CLI surfaced in this README.

---

## Table of Contents

1. [Why Sentinel?](#why-sentinel)
2. [Quickstart (for users)](#quickstart-for-users)
3. [Using SentinelKit in your project](#using-sentinelkit-in-your-project)
4. [CLI Overview](#cli-overview)
5. [Maintainer / contributor guide](#maintainer--contributor-guide)
6. [Slash Command Gates](#slash-command-gates)
7. [MCP Workflow](#mcp-workflow)
8. [Tests & CI](#tests--ci)
9. [Repository Layout](#repository-layout)
10. [Support & Resources](#support--resources)

---

## Why Sentinel?

Spec-Kit’s worldview is: **“the LLM does the work; specs help it behave.”**  
Sentinel-Kit’s worldview is stricter: **“the LLM does the work, but Sentinel decides what’s acceptable.”**

Specs are executable contracts, but the model should not be the judge of its own work. Sentinel-Kit pushes judgment into deterministic artifacts (contracts, context budgets, capsules, sentinel pytest suites) plus a CLI that runs them and emits a structured `selfcheck` report (`ok | pending | fail` per gate). MCP is the bridge that lets agents (Codex, Claude, etc.) call those tools directly, so the agent iterates like:

1. Change the repo.
2. Call sentinel tools.
3. Decide based on the external referee, not vibes.

You can still drive the CLI manually, but the happy path is “wire MCP so the agent asks Sentinel whether it’s allowed to continue.”

All of this runs on Python 3.12 via `uv`. Node tooling (pnpm, vitest, tsconfig) has been removed entirely.

---

## Quickstart

SentinelKit rides on top of GitHub's Spec‑Kit, but you do not need to clone or install the upstream project directly. Once you have [uv installed](https://docs.astral.sh/uv/getting-started/installation/), follow this flow whenever you want to start a new project:


# 1) Install the Specify CLI with Sentinel built-in
`uv tool install specify-cli --from git+https://github.com/llampwall/sentinel-kit.git`

# 2) Scaffold a project with Sentinel enabled
- choose your preferred assistant and shell - SentinelKit supports the options Spec-Kit exposes.
```bash
specify init <project-name> --sentinel`     
cd <project-name>
```
# 3) (Optional) Run Spec-Kit’s environment check
`specify check`

# 4) **(Recommended) Wire MCP so your agent can call Sentinel**
   ```bash
   codex mcp add sentinel -- uv run sentinel mcp server
   ```
   Open Codex in the repo; Sentinel tools become available automatically. `uv run sentinel selfcheck` will flip the `mcp` gate to `ok` once the client reaches the server.
# 5) **Iterate with `/speckit.*` commands as usual**
   - `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`
   - When Codex runs capsules, it can call Sentinel MCP tools between steps to decide whether to keep going.

> Need a one-off run without a global install? Use `uvx --from git+https://github.com/llampwall/sentinel-kit.git specify init <project-name> --sentinel`.

---

## Using SentinelKit in your project

Running `specify init --sentinel` adds SentinelKit assets alongside the standard Spec‑Kit scaffold:

- `.sentinel/**` with contracts, context budgets, prompts, and runbook templates
- `sentinelkit/` Python package pre-wired into the project environment
- CI snippets, decision ledger templates, and sentinel pytest suites

Inside a Sentinel-enabled repo:

- `specify check` runs Spec‑Kit's validation for the current repo.
- `uv sync` ensures the virtual environment matches the pinned dependencies in `uv.lock`.
- `uv run sentinel ...` executes SentinelKit commands (selfcheck, contracts, context lint, capsule operations, sentinel tests, MCP helpers, etc.).
- `uv run sentinel selfcheck` is the all-in-one guardrail we expect before commits land. Run it anytime you want SentinelKit's enforcement suite (contracts, context lint, capsule validation, sentinel tests, MCP smoke) to verify your repo.

Because `uv run` resolves against the project's lockfile, every repo uses the SentinelKit version it was scaffolded with, guaranteeing reproducible enforcement even if the global `specify` CLI updates later.

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

> **Need machine-readable output for CI?** Run `uv run sentinel --format json selfcheck > .artifacts/selfcheck.json` and upload the artifact alongside your test results. `specify check` uses the same JSON contract under the hood and fails only when a check reports `status="fail"`.

---

## MCP Tools Overview

- `mcp.sentinel.contract_validate` 
  * Validates a proposed change against the project’s contracts (schemas + fixtures) and returns structured pass/pending/fail details. 
  * CLI equivalent (roughly): `uv run sentinel contracts validate …` 
  * When an agent should call it: Before/after edits that touch contract-governed areas (API shapes, file formats, invariants) to decide “is this change allowed?”
- `mcp.sentinel.sentinel_run` 
  * Runs sentinel-marked pytest suites and returns a JSON summary (success flag, per-test stats, stdout/stderr). 
  * CLI equivalent (roughly): `uv run sentinel sentinels run …` 
  * When an agent should call it: When the agent needs to check “did I break anything important?” without running every test—ideal for per-task/pre-commit gates.
- `mcp.sentinel.decision_log` 
  * Appends a structured entry to `.sentinel/DECISIONS.md` (honors dry-run env vars) and returns the new entry. 
  * CLI equivalent (roughly): `uv run sentinel decisions append …` 
  * When an agent should call it: Whenever the agent makes a non-trivial trade-off/assumption and needs to record why, not just what, it changed. |

These tools are exposed automatically once the MCP server is configured.

---

## Maintainer / contributor guide

Working on SentinelKit itself? Clone the repo and use the bundled development workflow:

```bash
git clone https://github.com/llampwall/sentinel-kit.git
cd sentinel-kit
uv sync --dev
uv run sentinel selfcheck
uv run pytest -q
```

- `uv run sentinel selfcheck` exercises the same gates we recommend to end users, ensuring local changes do not break the contract/context/capsule/test stack.
- `uv run pytest -q` drives the Sentinel pytest suites directly.
- Maintainers who prefer a globally installed development copy can run `uv tool install --editable .` from the repo root, but this is optional and separate from the user-facing `specify` CLI install.

See [CONTRIBUTING.md](CONTRIBUTING.md) for additional guidelines.

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

Sentinel’s MCP server is the “external authority” endpoint. Without it, you must run `uv run sentinel …` yourself. With it, Codex (or any MCP-aware client) calls the same tools directly, which is how you get autonomous `/speckit.implement` loops.

### Manual mode (no MCP)

- Run `uv run sentinel selfcheck`, `uv run sentinel sentinels run`, etc. by hand.
- Useful when you want to stay in the loop, but agents cannot invoke those gates.

### Agent mode (with MCP)

- Register the server once per machine (Codex example):
  ```bash
  codex mcp add sentinel -- uv run sentinel mcp server
  ```
- Open Codex in the repo; Sentinel tools show up automatically.
- `uv run sentinel mcp smoke --format json` (already part of selfcheck) proves the handshake works.
- Other MCP clients can point to the same command via `.mcp.json` or their own CLI configuration.

Once configured, every capsule step can run: “apply change → call sentinel tools → only continue if `selfcheck` reports `ok`.” Pending gates are still allowed, but the agent now has a deterministic referee instead of scraping logs.

---

## Tests & CI

- **Bootstrap:** `uv sync --locked --dev` (with fallbacks), `uv run sentinel selfcheck`, `uv run pytest -q`.
- **Sentinel suites:** `uv run sentinel sentinels run --json-report test-results/sentinels.json --junit test-results/sentinels.xml`.
- **MCP smoke:** `uv run sentinel mcp smoke --format json`.
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
- [Spec‑Kit docs](https://github.com/github/spec-kit#readme) – the upstream spec rails that Sentinel-Kit enforces. Always start there for `/speckit.*` behaviors, then layer Sentinel gates on top.
- `.sentinel/snippets/*` – reusable snippets for README badges, MCP guidance, capsules, etc.

If you find issues or have feature requests, open an issue or pull request on GitHub—just make sure `uv run sentinel selfcheck` is green first.

---

Happy shipping! The whole point of Sentinel-Kit is to give you deterministic guards so your specs stay true across repos, operating systems, and agents. If `selfcheck` passes, you’re good to merge. !*** End Patch
