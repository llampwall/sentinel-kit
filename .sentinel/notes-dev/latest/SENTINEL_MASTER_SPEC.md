# Sentinel‑Kit Master Spec

## 1. Overview

Sentinel‑Kit is an opinionated extension of GitHub Spec‑Kit that adds capsules, task‑specific agents, and an enforcement layer (contracts, sentinel tests, decision ledger, MCP tools) on top of Spec‑Kit’s spec‑driven development rails.

Sentinel‑Kit does **not** replace Spec‑Kit. For end users, projects created with:

```bash
specify init <NAME> --sentinel
```

behave like normal Spec‑Kit projects (constitution → spec → plan → tasks → implement), but gain:

- Capsule‑based task execution.
- Router + task‑specific agents with explicit roles and playbooks.
- Enforcement via contracts, sentinel tests, context limits, and a decision ledger.
- An MCP server exposing Sentinel tools to AI coding agents (Codex, Claude Code, Cursor, etc.).

This spec defines the functional behavior and capabilities of Sentinel‑Kit in terms of:

1. Scaffolding & CLI integration.
2. Capsules as task containers.
3. Agent framework (Router + task‑specific agents).
4. Sentinel enforcement (contracts, tests, decision ledger, context).
5. MCP server and tools for coding agents.
6. Template integration with Spec‑Kit phases.
7. Non‑functional and integration requirements.

Implementation details (Python module layout, specific libraries) are intentionally out of scope.

---

## 2. Personas and Goals

### 2.1 Personas

- **Spec‑Kit user / maintainer**
  - Uses Spec‑Kit to define specs, plans, and tasks.
  - Wants guardrails against “vibe‑coding” when working with AI agents.
  - Cares about contracts, tests, provenance, and long‑term maintainability.

- **AI coding agent**
  - Executes `/speckit.*` commands and implements tasks.
  - Interacts with Sentinel via CLI and MCP tools.
  - Needs clear constraints (Allowed Context, contracts, tests) to decide when work is “done”.

- **Project maintainer / reviewer**
  - Reviews PRs and change sets.
  - Wants deterministic signals (contracts/tests/selfcheck) and a decision ledger that explains why changes exist.

### 2.2 Goals

- Make `specify init <NAME> --sentinel` feel like standard Spec‑Kit to humans, while:
  - Constraining agents to capsule‑defined context and acceptance.
  - Surfacing contracts, sentinel tests, and decision ledger as first‑class gates.
  - Enabling IDE / MCP clients to call Sentinel tools during `/speckit.implement`.

- Keep Sentinel‑Kit vendor‑agnostic:
  - Work across IDEs and CLIs that support slash commands and/or MCP.
  - Avoid entangling behavior with any single LLM provider.

---

## 3. Scaffolding & CLI Integration

### 3.1 Sentinel‑enabled project scaffolding

When a user runs:

```bash
specify init <NAME> --sentinel
```

the CLI must:

1. **Apply the standard Spec‑Kit template** for the chosen AI assistant and script type.
2. **Apply Sentinel‑Kit scaffold** on top of the template by copying assets from `src/sentinel_assets/**` into the new project:

   - `.sentinel/**` directory, including:
     - `agents/**` – ROLE/PLAYBOOK/prompt definitions and metadata for:
       - Router (required).
       - Builder, Frontender, Backender, Designer, CapsuleAuthor, Verifier, Integrator, Refactorer, Scribe, Observer, Releaser, Commander, and other supported roles.
     - `.sentinel/tests/sentinels/**` – default sentinel pytest suites.
     - `.sentinel/contracts/**` – versioned schemas and fixtures for HTTP APIs, data models, and other contracts.
     - `.sentinel/context/**` – context limits and lint configuration.
     - `.sentinel/docs/**` – runbook and implementation templates.
     - `.sentinel/status/**` – status and MCP smoke artifacts.
     - `.sentinel/snippets/**` – reusable README / MCP / workflow snippets.
     - `.sentinel/DECISIONS.md` – decision ledger.

   - `sentinelkit/` Python package directory:
     - Wiring Sentinel‑Kit’s CLI, MCP server, and helpers into the repo’s Python environment.

   - `.github/workflows/sentinel-ci.yml`:
     - Reference CI workflow that runs `uv sync`, `uv run sentinel selfcheck`, sentinel tests, and MCP smoke.

   - Agent prompt bundles:
     - Copy `.sentinel/prompts/**` into the appropriate agent‑specific bundle (e.g., `.codex/prompts/sentinel.router.md`) for the selected assistant.

3. **Wire Sentinel into the project environment**:

   - Ensure `pyproject.toml` and `uv.lock` include the sentinelkit package and dependencies.
   - Ensure `uv sync` in the project root creates a venv that can run `uv run sentinel …`.

### 3.2 CLI behavior

- `specify check` must continue to behave like Spec‑Kit’s standard `specify check`:
  - It may call `uv run sentinel selfcheck` under the hood.
  - Sentinel‑specific failures should surface as additional checks, not as a change in semantics of existing Spec‑Kit checks.

- Sentinel CLI entrypoint:

  ```bash
  uv run sentinel <subcommand> [options]
  ```

  must provide:

  - `sentinel selfcheck` – composite gate that runs contracts, context lint, capsules validation, sentinel tests, and MCP smoke.
  - `sentinel contracts validate` – contract and fixture validation.
  - `sentinel context lint` – enforce Allowed Context and budgets.
  - `sentinel sentinels run` – run sentinel pytest suites and emit structured JSON.
  - `sentinel decisions append` – append structured entries to `.sentinel/DECISIONS.md`.
  - `sentinel runbook append` – append implementation notes to `.sentinel/docs/IMPLEMENTATION.md`.
  - `sentinel mcp server` and `sentinel mcp smoke` – MCP server and smoke test.

The spec does not constrain CLI flags beyond requiring machine‑readable `--format json` modes and consistent behavior between CLI and MCP tools.

---

## 4. Capsules as Task Containers

### 4.1 Capsule structure

Sentinel‑Kit expects capsules to be stored under:

```text
.specify/specs/<id>/capsule.md
```

Each capsule must include, in a structured and parseable form:

- **Goal** – concise description of what the task is meant to achieve.
- **Acceptance Criteria** – clear, testable conditions for “done”.
- **Allowed Context** – list of file globs or paths the agent is allowed to read.
- **Required Outputs** – paths and formats of artifacts the agent must produce or update.
- **Provenance metadata** – capsule ID, related spec/plan/tasks, prior decisions where relevant.

Templates and prompts under `.sentinel/prompts/**` must guide CapsuleAuthor to fill out these sections consistently.

### 4.2 Capsule usage rules

- Non‑trivial work must be anchored to a capsule; ad‑hoc edits without capsule context are discouraged and should not be considered “Sentinel‑safe.”
- Agents must treat Allowed Context as a hard allowlist:
  - They may read files explicitly listed or covered by Allowed Context.
  - Reading arbitrary files outside Allowed Context is considered a violation.
- Capsules should be **small and composable**:
  - Focused on a single feature, fix, or refactor.
  - Encourage follow‑up capsules instead of large, multi‑week kitchen‑sink tasks.

### 4.3 Capsule authoring and updates

- Sentinel‑Kit must provide helpers (CLI commands and prompts) that:
  - Help CapsuleAuthor create new capsules based on specs and plans.
  - Suggest Allowed Context based on touched files or dependencies.
  - Emit initial Required Outputs and provenance stubs.

- When features evolve:
  - Capsules should be updated or superseded rather than silently drifting.
  - Decision ledger entries should cross‑link capsules that introduce or change significant behavior.

---

## 5. Agent Framework (Router + Task‑Specific Agents)

### 5.1 Agent discovery

Sentinel‑Kit must support dynamic discovery of agents under:

```text
.sentinel/agents/<agent_id>/
```

Each agent directory includes:

- `agent.json` – machine‑readable metadata:

  ```json
  {
    "id": "builder",
    "name": "Builder",
    "rulesHash": "…",
    "summary": "Implements changes under a capsule",
    "routing_keywords": ["implement", "code", "refactor"],
    "mount_paths": ["src/**", "tests/**", ".sentinel/**"],
    "prompt_files": ["ROLE.md", "PLAYBOOK.md"]
  }
  ```

- `ROLE.md` – mission, in‑scope/out‑of‑scope work, required outputs, quality bar, escalation rules.
- `PLAYBOOK.md` – step‑by‑step capsule execution instructions.

Sentinel‑Kit must not hard‑code agent names; Router and tooling should operate over discovered `agent.json` entries.

### 5.2 Router behavior

The Router agent is required for Sentinel flows. Functionally, Router must:

- Read the current capsule (Goal, Acceptance, Allowed Context, Required Outputs).
- Optionally consider routing hints (e.g., `routing_keywords` from `agent.json`).
- Select **one** lead agent for the capsule.
- Declare:
  - Which mount_paths from the selected agent to honor.
  - Which files to expose based on capsule Allowed Context.
  - The Required Outputs the agent is responsible for.

The spec does not dictate whether Router runs inside `/speckit.implement` or as a separate command, but conceptually:

- `/speckit.implement` invokes Router whenever it needs to assign a capsule to an agent.
- Router’s decision is traceable (e.g., via logs or capsule annotations).

### 5.3 Task‑specific agents

Non‑Router agents implement work within their ROLE constraints:

- **Builder / Frontender / Backender** – implement features in code.
- **Designer** – produce design tokens and UX specs.
- **CapsuleAuthor** – write and update capsules.
- **Verifier** – own tests and contracts related to a change.
- **Integrator / Refactorer** – integrate changes, reshape code while preserving behavior.
- **Scribe** – update docs, runbooks, and changelogs.
- **Releaser / Commander / Observer** – orchestrate releases, long‑running tasks, or monitoring.

Each agent:

- Accepts a capsule and Router‑defined mounted context.
- Follows its PLAYBOOK, including:
  - When to call Sentinel MCP tools.
  - When to request new capsules or escalate instead of stretching scope.
  - How to stamp outputs with provenance headers.

Agents besides router are OPTIONAL, though CapsuleAuthor and Verifier are integral to a "hands-off" agentic workflow.

### 5.4 Invocation model

Within `/speckit.implement` and related flows:

- Agents are invoked as *roles*, not as ad‑hoc prompts:
  - The IDE or CLI selects Router and then the chosen agent, passing capsule + context.
  - Agents interact with the repo via Sentinel’s expected operations (edit files, run CLI commands, call MCP tools).

The spec leaves exact IDE integration details open; it only requires that the agent model (Router + roles + capsules) is respected.

---

## 6. Sentinel Enforcement: Contracts, Tests, Decision Ledger, Context

### 6.1 Contracts and fixtures

Sentinel‑Kit must support a contracts layer for:

- HTTP APIs and RPC interfaces.
- Data models, file formats, and external dependencies.

Contracts consist of:

- Versioned schemas under `.sentinel/contracts/**`.
- Fixtures under `.sentinel/contracts/fixtures/**`.

The `sentinel_contract_validate` tool (and its CLI equivalent) must:

- Validate all or selected fixtures against their schemas.
- Return structured results (per‑fixture `ok` + errors).
- Be callable from:
  - CLI (`uv run sentinel contracts validate …`).
  - MCP (`sentinel_contract_validate`).

### 6.2 Sentinel tests

Sentinel tests are pytest suites under `.sentinel/tests/sentinels/**` that encode:

- Critical behaviors and guardrails.
- Regressions tied to specific features or decisions.

The `sentinel_run` tool (and CLI `sentinel sentinels run`) must:

- Discover and run sentinel tests.
- Return:
  - `ok` flag.
  - Exit code.
  - Summary of test results.
  - Paths of reports (JSON, JUnit) when requested.

Sentinel tests must be treated as higher‑signal than generic tests for enforcement decisions, but they do not replace the project’s broader test suite.

### 6.3 Decision ledger and provenance

The decision ledger (`.sentinel/DECISIONS.md`) stores structured entries describing:

- The decision ID.
- Author / agent.
- Scope (files or areas affected).
- Decision text and rationale.
- Outputs (paths touched).
- RulesHash / version of rules in effect.
- Optional date and related capsules/specs.

The `sentinel_decision_log` tool (and CLI `sentinel decisions append`) must:

- Append entries to the ledger, with optional dry‑run / preview modes.
- Return:
  - The new decision ID.
  - Paths to ledger and preview.
  - Snippets for embedding ProducedBy / RulesHash / Decision / Related‑Capsule headers in code or docs.

Agents must use this tool for meaningful trade‑offs and design decisions, not for trivial edits.

### 6.4 Context limits and lint

Sentinel‑Kit must include a context linting mechanism that:

- Reads capsule Allowed Context and default budgets from `.sentinel/context/**`.
- Checks that:
  - Accessed files fall within Allowed Context.
  - Context size / line budgets are within configured limits.

The `sentinel context lint` command must:

- Be callable per capsule or per repo.
- Produce machine‑readable results (e.g., per path status).
- Integrate into selfcheck and CI enforcement.

### 6.5 Selfcheck and quality gates

`sentinel selfcheck` must aggregate:

- Contracts validation.
- Context lint.
- Capsule validation (structure, Allowed Context, Required Outputs).
- Sentinel tests.
- MCP smoke (`sentinel mcp smoke`) to verify MCP connectivity.

It returns:

- A per‑gate status (`ok` / `pending` / `fail`).
- A top‑level `ok` flag.

Projects and CI should treat `selfcheck` as the primary gate for “is this repo in a sentinel‑compliant state?”.

---

## 7. MCP Server and Tools for Coding Agents

### 7.1 MCP server process

Sentinel‑Kit must provide an MCP server process, typically invoked as:

```bash
uv run sentinel mcp server
```

The server:

- Uses newline‑delimited JSON‑RPC over stdio.
- Implements MCP’s `initialize`, `tools/list`, `tools/call`, `shutdown`, and `exit` methods.
- Exposes Sentinel tools to MCP‑capable clients (Codex, MCP Inspector, etc.).

### 7.2 Tools

At minimum, the server must expose:

- `sentinel_contract_validate`
  - Inputs (params):
    - Optional `contract` identifier (e.g., `users.v1`).
    - Optional `fixture` path for targeted validation.
  - Outputs:
    - `ok` flag.
    - `results`: per‑fixture contract results.

- `sentinel_run`
  - Inputs:
    - Optional `marker` / filter for test selection.
  - Outputs:
    - `ok` flag.
    - `exit_code`.
    - Summary of executed tests, with counts and (optionally) report paths.

- `sentinel_decision_log`
  - Inputs:
    - `author`, `scope`, `decision`, `rationale`, `outputs`.
    - Optional: `supersedes`, `date`, `agent`, `rules_hash`, `dry_run`, `preview`, `decision_id`.
  - Outputs:
    - Decision ID.
    - Ledger path.
    - Preview path (if dry‑run).
    - Snippets for ProducedBy / RulesHash / Decision / Related‑Capsule in multiple languages.

Tool names must comply with MCP / LLM tool naming rules (alphanumeric, underscore, hyphen) so they can be forwarded to OpenAI tools APIs without renaming.

### 7.3 Usage from agents

Within `/speckit.implement` and related flows, agents should:

- Call `sentinel_contract_validate`:
  - Before or after changes that touch contract‑governed areas.
- Call `sentinel_run`:
  - Before declaring a capsule “done”, to ensure sentinel tests pass.
- Call `sentinel_decision_log`:
  - Whenever a non‑trivial decision or trade‑off is made.

These calls should be part of the agent’s PLAYBOOK “definition of done” rather than optional extras.

---

## 8. Template Integration with Spec‑Kit Phases

### 8.1 Constitution / spec / plan / tasks

For Sentinel‑enabled projects, Spec‑Kit templates must be extended so that:

- **Constitution** mentions Sentinel’s role:
  - Capsules as mandatory contexts for non‑trivial work.
  - Contracts, tests, and decision ledger as gates.

- **Spec** documents:
  - Feature requirements and user‑facing behavior.
  - Links to relevant capsules and contracts when known.

- **Plan** explains:
  - How Sentinel enforcement applies to this feature (e.g., new contracts, tests, context changes).
  - Any required agent roles (e.g., Designer + Builder + Verifier).

- **Tasks** include:
  - Steps for updating/adding contracts and fixtures.
  - Steps for writing/updating sentinel tests.
  - Steps for running Sentinel checks (CLI or MCP).
  - Steps for logging decisions and adding provenance headers.

### 8.2 Implement prompts

Implementation prompts (for `/speckit.implement` and adjacent flows) must instruct agents to:

- Work from capsules and respect Allowed Context.
- Let Router select the lead agent and mounted paths.
- Use relevant agents (Builder, Frontender, Backender, Verifier, Scribe, etc.) according to ROLE/PLAYBOOK.
- Call Sentinel MCP tools as part of completing tasks.
- Stamp outputs with provenance headers derived from `sentinel_decision_log`.

The templates should remain IDE‑agnostic (no direct references to a specific client), but they should mention MCP tool usage conceptually.

---

## 9. Non‑Functional and Integration Requirements

### 9.1 Vendor‑agnostic

Sentinel‑Kit must:

- Work with any IDE/agent that supports:
  - Slash commands mapped to CLI invocations, and/or
  - MCP stdio servers.
- Avoid dependencies on proprietary features of a single provider.

### 9.2 Minimal setup overhead

- Installing Sentinel‑Kit should be as close as possible to:

  ```bash
  uv tool install specify-cli --from git+https://github.com/llampwall/sentinel-kit.git
  ```

- Projects created with `--sentinel` should “just work”:
  - `uv sync` sets up the environment.
  - `specify check` + `uv run sentinel selfcheck` run without manual wiring.
  - MCP registration is documented and, where possible, pre‑seeded (e.g., Codex `.codex/config.toml`).

### 9.3 Performance and context usage

- ROLE/PLAYBOOK prompts and capsules must be designed to fit within typical context windows for modern code models; they should:
  - Favor concise, structured instructions.
  - Avoid embedding entire repos when Allowed Context is sufficient.

- Sentinel tests and contracts should be:
  - Incremental and composable (per feature/area), not monolithic “run everything always”.
  - Fast enough to run frequently during development and in CI.

### 9.4 Out‑of‑scope for this spec

The following are explicitly future work and must be addressed via separate specs:

- Multi‑repo orchestration and cross‑repo contracts.
- Web dashboards or UIs for visualizing capsules, agents, and decisions.
- Long‑running autonomous agents planning entire roadmaps without human oversight.
- Deep integration with any single LLM provider beyond standard MCP and HTTP APIs.

---

## 10. Primary User Flows

### 10.1 Initialize and run through Spec‑Kit phases

1. User installs Sentinel‑Kit‑backed Specify CLI via `uv tool install …`.
2. Runs `specify init <NAME> --sentinel`:
   - Base Spec‑Kit template + Sentinel assets are scaffolded.
   - `.sentinel/**`, `sentinelkit/`, agent bundles, and CI files are created.
3. Runs `uv sync` in the project root.
4. Runs:
   - `/speckit.constitution` to refine the project constitution (which refers back to Sentinel’s role).
   - `/speckit.specify`, `/speckit.plan`, `/speckit.tasks` to create specs and plans.
5. Runs `uv run sentinel selfcheck` to ensure initial contracts/tests/context/MCP gates are green.

### 10.2 Add a new feature capsule and run Router + agents + gates

1. A new feature is requested and captured in Spec‑Kit spec/plan/tasks.
2. CapsuleAuthor creates a new capsule under `.specify/specs/<id>/capsule.md`:
   - Defines Goal, Acceptance Criteria, Allowed Context, Required Outputs.
3. Router is invoked (e.g., via `/speckit.implement`):
   - Reads the capsule.
   - Selects the appropriate agent (e.g., Builder + Backender).
   - Declares mounted context and outputs.
4. Lead agent executes the capsule:
   - Edits code and tests within Allowed Context.
   - Calls `sentinel_contract_validate` and `sentinel_run` via MCP or CLI.
   - Uses `sentinel_decision_log` to record key decisions and obtain provenance headers.
5. Verifier (or the same agent, depending on ROLE) ensures:
   - Sentinel checks pass (`sentinel selfcheck` or equivalent subset).
   - Required Outputs exist and match the capsule.
6. Capsule is marked accepted (by human or Router), and tasks are updated accordingly.

This flow must be achievable using only:

- Standard Spec‑Kit commands.
- Sentinel CLI (`uv run sentinel …`).
- Sentinel MCP tools in an MCP‑capable IDE/agent.

