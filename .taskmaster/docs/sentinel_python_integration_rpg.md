# PRD (RPG) — Sentinel‑Kit: Python‑Only Integration into Spec‑Kit (Windows/Linux/macOS)
<!-- For context you can show Codex:

Spec-Kit’s Specify CLI is the official init path we’re integrating with. 
https://github.com/github/spec-kit

Task Master’s PRD + parsing flow (quick start / intro / tasks) matches the structure here. 
https://docs.task-master.dev/getting-started/quick-start/quick-start
https://docs.task-master.dev/capabilities/rpg-method

uv is the recommended fast Python project manager we’re standardizing on. 
https://docs.astral.sh/uv/

If you want a DECISIONS.md seed and the pyproject.toml/Typer CLI skeleton added under the PRD in the canvas, say the word and I’ll drop those next. -->


> **Standard:** Task Master PRD + RPG format (author this file under `.taskmaster/docs/sentinel_python_integration_rpg.md` and parse with `task-master parse-prd`).

<overview>
## Problem Statement
Sentinel‑Kit currently ships Node-based utilities that complicate a Python‑first Spec‑Kit workflow and create brittle onboarding (Windows path quirks, pnpm config, split toolchains). We need Sentinel‑Kit to be **pure Python**, integrated end‑to‑end into Spec‑Kit’s flow and scaffolded directly by the **Specify CLI**. After initialization, a fresh clone on Windows/Linux/macOS must run a single bootstrap and pass all gates (contracts, context checks, sentinel tests, MCP smokes) with no Node.js, pnpm, or PowerShell dependencies.

## Target Users
- Spec‑Kit adopters who want a zero‑drama, Python‑native enforcement layer.
- Maintainers who need deterministic local setup and CI across OSes.
- AI‑assisted workflows (Codex/Cursor/Claude Code) that rely on Spec‑Kit’s `/speckit.*` flow and expect consistent gates.

## Success Metrics
- Fresh scaffold via `specify init --sentinel` → one Python bootstrap → green on Win/Linux/macOS.
- **No `node_modules`, no pnpm, no PowerShell**; a single Python toolchain via **uv**.
- `/speckit.*` commands run Sentinel gates automatically; failures are actionable.
- Parity: Python validators match legacy outputs (where applicable); Node enclave fully removed.
</overview>

<functional-decomposition>
## Capability Tree

### Capability: Python Enforcement Primitives
Replace JS tools with Python CLIs and libraries.

#### Feature: Contract Validation (Python)
- **Description**: Validate fixtures against versioned contracts via a Python CLI and MCP server.
- **Inputs**: `sentinel/contracts/*.yaml`, `sentinel/contracts/fixtures/**`.
- **Outputs**: JSON/pretty report; non‑zero exit on failure.
- **Behavior**: Pydantic/JSONSchema or Yamale-based schema validation; deterministic ordering; machine‑readable errors.

#### Feature: Sentinel Tests (Python)
- **Description**: Sentinel regression suites (pytest) encoding past bugs.
- **Inputs**: Fixtures + adapters under `tests/sentinels/**`.
- **Outputs**: Pytest report (JSON plugin + JUnit XML for CI); non-zero exit on failure.
- **Behavior**: Taggable tests (`@pytest.mark.sentinel`), selective runs by domain.

#### Feature: Allowed Context & Capsule Generation
- **Description**: Port Allowed Context discovery, context limits linting, capsule generator, and associated docs automation (md-surgeon snippets) to Python.
- **Inputs**: Shipping context under `.sentinel/context/**` (not maintainer-only notes-dev), context limits schema, `.specify/specs/<slug>/{spec,plan,tasks}.md`.
- **Outputs**: Deterministic Allowed Context list, lint diagnostics, capsule markdown, prompt logs; hard fail when paths escape or exceed 300 lines.
- **Behavior**: Path normalization via `pathlib`, glob support, JSON diagnostics for slash commands, deterministic ordering identical to the legacy JS tooling.

#### Feature: Decision Ledger & Provenance (Python)
- **Description**: Append `DECISIONS.md` entries and emit `ProducedBy=` headers via a Python CLI/MCP.
- **Inputs**: decision metadata (author, scope, rationale).
- **Outputs**: Ledger entry + header snippet for commit messages or file headers.

### Capability: Spec-Kit Flow Integration
Make Sentinel an invisible augmentation of the standard flow.

#### Feature: `specify init --sentinel`
- **Behavior**: Extend the Typer CLI to accept `--sentinel`, copy Sentinel Python package files (pyproject, sentinelkit package, context docs, MCP config, CI workflow, README badge/snippet), and run a post-init bootstrap (`uv sync && sentinel selfcheck`). No Node artifacts land in the scaffold.

#### Feature: `specify check`
- **Behavior**: Run the Sentinel CLI health check (tool versions, uv cache, MCP smoke scripts) so contributors catch tooling issues before invoking `/speckit.*`.

#### Feature: `/speckit.constitution` Gate
- **Behavior**: After constitution is generated, run `sentinel contracts validate` and `sentinel context lint` to fail fast when scaffolds drift.

#### Feature: `/speckit.specify` Gate
- **Behavior**: Validate contracts + context; run the Python capsule generator; only emit capsules when green and surface lint errors inline.

#### Feature: `/speckit.plan` & `/speckit.tasks` Gates
- **Behavior**: Preflight validation before plan/task emission; annotate failures with file paths and suggested fixes; rerun capsule/context lint automatically.

#### Feature: `/speckit.implement` Gate
- **Behavior**: Block merges when sentinel tests or contract validation fail; emit minimal diff hints for agents; ensure MCP smokes pass before completion.

#### Feature: `/speckit.clarify`
- **Behavior**: Capture every `[NEEDS CLARIFICATION]` marker as a decision ledger entry and capsule Router Note via the Python CLI/MCP so ambiguity never lives only in chat.

#### Feature: `/speckit.analyze`
- **Behavior**: Run the prompt renderer in analysis mode to diff `spec.md`, `plan.md`, `tasks.md`, and the capsule; emit structured drift diagnostics and re-run context lint when mismatches occur.

#### Feature: `/speckit.checklist`
- **Behavior**: Generate acceptance checklists from capsule criteria + sentinel coverage gaps; persist them next to the capsule and enforce completion before `/speckit.implement` succeeds.

#### Feature: Agent Prompt Scaffolding
- **Behavior**: When `specify init --sentinel` runs (for Codex/Claude/Cursor/etc.), copy or symlink the canonical Sentinel prompt templates (`.sentinel/prompts/*.md`, `.sentinel/prompts/*.eta.md`, `.sentinel/templates/capsule.md`) into the agent bundle (e.g., `.codex/prompts/speckit.plan.md`, `.codex/prompts/speckit.analyze.md`, `/speckit.implement.md`, etc.) so every slash command uses the new Sentinel-aware guidance. Keep these templates in sync via md-surgeon/snippets.
- **Inputs**: `.sentinel/prompts/**`, `.sentinel/templates/capsule.md`, agent bundle directories like `.codex/prompts/`.
- **Outputs**: Agent-specific prompt files that reference Sentinel CLI steps, capsule paths, and enforcement checklists.

#### Feature: Implementation Runbook
- **Description**: Scaffold `.sentinel/docs/IMPLEMENTATION.md` as a living report capturing the current enforcement surface, execution flow, known gaps, CI/stack context, and architecture decisions. `/speckit.plan` and `/speckit.implement` (or CapsuleAuthor) append stack-specific notes automatically, so newcomers can see “how everything fits together” without spelunking the repo.
- **Inputs**: Outputs from plan/tasks/implement phases, decision log entries, stack choices.
- **Outputs**: Updated runbook committed to the repo; referenced by README/status docs; optionally exposed in capsules when relevant.
- **Behavior**: Template sections (Current Enforcement Surface, Execution Flow, Known Gaps, CI Workflow, Stack Context). Provide CLI helper (e.g., `sentinel runbook append --section stack --note ...`) to keep updates structured.

#### Feature: Prompt Renderer
- **Behavior**: Replace the Node renderer with a Python CLI that renders router/agent prompts from Eta-equivalent templates, validates router JSON, writes logs/snippets, and is callable from slash commands.

#### Feature: Agent Roster & Capsule Authoring
- **Behavior**: Keep `.sentinel/agents/<role>/` folders as the source of truth for agent ROLE/CHECKLIST/PLAYBOOK files. Router auto-discovers available agents at runtime; teams can add/remove agents (Integrator, Designer, CapsuleAuthor, etc.) per repo without code changes. Provide guidance + tooling so CapsuleAuthor can automatically create/update capsules when agents discover scope gaps, enabling closed-loop `/speckit.implement` runs.
- **Inputs**: `.sentinel/agents/**`, router JSON, capsule templates.
- **Outputs**: Dynamic agent roster JSON, CapsuleAuthor workflows for patching capsules and logging decisions.

### Capability: MCP Surfaces (Python)
Expose small, deterministic tools for agents without inflating context.

- `mcp.sentinel.contract_validate` – keep the initialize → tools/list → tools/call handshake and smoke tests identical to the Node server, validating specific IDs/paths on demand.
- `mcp.sentinel.sentinel_run` – execute only sentinel-marked pytest suites and return the Vitest-style JSON summary (success flag, stats, stdout/stderr) agents already consume.
- `mcp.sentinel.decision_log` – append ledger entries, return the ProducedBy header snippet, and honor dry-run env vars while propagating CLI errors.

### Capability: Bootstrap & CI (Python-only)
- Single bootstrap command using **uv** (`uv sync`), then `sentinel selfcheck` (contracts, context lint, capsule generator, sentinel pytest marker, MCP smokes) and pytest JSON reports.
- GitHub Actions matrix: Windows, Linux, macOS; uses uv caching, replaces `.github/workflows/sentinel-kit.yml`, runs all Sentinel gates, and uploads artifacts for failures.
- `specify check` runs the same Sentinel health checks locally (tool versions, uv cache, MCP smokes) before any slash command is invoked.

<structural-decomposition>
## Structural Modules (Python‑only)

```
/.taskmaster/docs/sentinel_python_integration_rpg.md   # this PRD
/.tool-versions                                        # python pin only (e.g., 3.12.x)
/.github/workflows/sentinel-ci.yml                     # OS matrix (uv + pytest + CLIs)
/README.md                                             # one‑click Python section
/DECISIONS.md                                          # decision ledger (Python CLI updates)
/sentinelkit/                                          # Python package (the library)
  __init__.py
  contracts/
    __init__.py
    schemas/                                           # YAML/JSON schemas
    fixtures/                                          # sample fixtures for tests
  context/
    __init__.py
    allowed_context.py                                 # discovery + normalization + glob safeguards
    limits.py                                          # context limits schema loader
    lint.py                                            # CLI/Slash command entry point
  capsule/
    __init__.py
    generator.py                                       # hydrate spec/plan/tasks into capsule.md
    templates/                                         # Eta-equivalent router/agent templates
  prompt/
    __init__.py
    render.py                                          # router/agent prompt renderer + JSON validator
  cli/
    __init__.py
    main.py                                            # `python -m sentinelkit ...`
    contract_validate.py
    context_lint.py
    decision_log.py
    mcp/
      __init__.py
      server.py                                        # JSON‑RPC over stdio
  utils/
    __init__.py
    io.py, errors.py, jsonfmt.py
  scripts/
    __init__.py
    md_surgeon.py                                      # Markdown snippet management (README/UPSTREAM/etc.)
/tests/
  conftest.py
  sentinels/                                           # pytest suites
  fixtures/                                            # mirrored test data
/pyproject.toml                                        # uv/pep 621; entry points
.sentinel/prompts/                                     # Canonical router/agent templates (.md + .eta) synced into agent bundles
.sentinel/templates/capsule.md                         # Capsule template used by generator + agent scaffolds
.sentinel/agents/**                                    # Configurable agent roster (Router, CapsuleAuthor, Integrator, Designer, etc.)
.sentinel/docs/IMPLEMENTATION.md                       # Generated runbook capturing enforcement surface + stack context
.codex/prompts/, .claude/prompts/, etc.                # Agent-specific prompt directories populated from Sentinel templates
```

**CLI entry points (pyproject):**
```
[project.scripts]
sentinel = "sentinelkit.cli.main:app"        # Typer‑based root
```

**Commands** (examples):
- `sentinel contracts validate [--id ... | --path ...] [--format json]`
- `sentinel context lint [--capsule <path>]`
- `sentinel sentinels run [--k marker=sentinel]`
- `sentinel decisions append --id D-XXXX --scope path1 path2 --rationale ...`
- MCP server: `python -m sentinelkit.cli.mcp.server`

**Spec‑Kit integration points** (called by Specify CLI and slash commands):
- Post‑init hook for `specify init --sentinel` runs `uv sync && sentinel selfcheck`.
- Slash commands invoke gates via lightweight Python subprocess calls.
</structural-decomposition>

<dependency-graph>
## Dependency Graph (Topological)

1. **Phase 0 — Foundations**
   - P0.1: Confirm Spec-Kit upstream shape; identify init hook for `--sentinel`.
   - P0.2: Add Python package skeleton (`pyproject.toml`, `sentinelkit/`, `tests/`).
   - P0.3: CI workflow with uv cache and OS matrix.
   - P0.4: Replace md-surgeon usage with a Python snippet tool and ensure README/UPSTREAM badge blocks are generated via snippets.
   - P0.5: Extend `specify check` to invoke the Sentinel CLI health checks (tool versions, uv cache, MCP smokes).

2. **Phase 1 — Enforcement Primitives (Python)**
   - P1.1: Implement contract validator (schemas + fixtures + CLI + MCP).
   - P1.2: Implement decision ledger appender and provenance header.
   - P1.3: Port sentinel tests to pytest; add `-m sentinel` marker and JSON reporter.
   - P1.4: Port Allowed Context linter, capsule generator, prompt renderer, and docs automation to Python.

3. **Phase 2 — Spec‑Kit Flow Wiring**
   - P2.1: `specify init --sentinel` bundles Python package stubs + CI + README block; post‑init runs `uv sync && sentinel selfcheck`.
   - P2.2: Wire `/speckit.*` commands (constitution/specify/plan/tasks/clarify/analyze/checklist/implement) to call Sentinel gates (contracts, context lint, capsule generator, prompt renderer, sentinel pytest); ensure helpful failure copy and actionable remediation hints.
   - P2.3: Ensure agent prompt bundles (e.g., `.codex/prompts/speckit.*.md`) are generated from the canonical Sentinel templates so every agent sees the same instructions.
   - P2.4: Document and implement dynamic agent discovery (`.sentinel/agents/**`), including guidance for CapsuleAuthor to patch capsules mid-flight when routers/agents uncover gaps.
   - P2.5: Generate and maintain `.sentinel/docs/IMPLEMENTATION.md` via CLI helpers so plan/implement phases log architecture/stack decisions in a structured runbook.

4. **Phase 3 — MCP Surfaces**
   - P3.1: JSON-RPC stdio server exposing contract_validate/sentinel_run/decision_log.
   - P3.2: Smoke tests: initialize → list tools → call → structured pass/fail.

5. **Phase 4 — Removal of Node Enclave**
   - P4.1: Delete `.sentinel/` JS workspace, pnpm configs, and any PowerShell installers.
   - P4.2: Add DECISION entry documenting deprecation and migration.

6. **Phase 5 — Linux Hardening**
   - P5.1: Ensure POSIX paths/shell usage; verify no Windows-only assumptions.
   - P5.2: Add distro notes (Ubuntu/Fedora) for `uv` install; confirm selfcheck green.

</dependency-graph>

<execution-order>
## Phase Breakdown & Deliverables

### Phase 0 — Foundations
- **Deliverables**: `pyproject.toml`, package skeleton, CI workflow using uv; README “Python-only” note; `.tool-versions` with Python pin; Python md-surgeon replacement + snippet imports; `specify check` wired to Sentinel health checks.
- **Exit**: `uv sync` works on Win/Linux/macOS.

### Phase 1 — Enforcement Primitives
- **Deliverables**: `sentinel contracts validate`, `sentinel decisions append`, pytest sentinel suites, Allowed Context linter, capsule generator, prompt renderer; MCP stubs.
- **Exit**: Local green suite; JSON outputs stable.

### Phase 2 — Spec-Kit Flow Wiring
- **Deliverables**: Specify-CLI `--sentinel` flag integration; post-init bootstrap; slash-command gates (constitution/specify/plan/tasks/implement plus clarify/analyze/checklist) invoking Python CLIs; agent prompt bundles synced with `.sentinel/prompts/**`; dynamic `.sentinel/agents/**` discovery + CapsuleAuthor guidance; `.sentinel/docs/IMPLEMENTATION.md` runbook template + CLI helper; updated README/UPSTREAM instructions via snippets.
- **Exit**: Fresh scaffold + `uv sync && sentinel selfcheck` + green; `/speckit.*` flows block on failures with actionable errors and logged clarifications; newly scaffolded agent folders reuse the Sentinel prompt templates and expose the configurable roster; the runbook reflects current stack/enforcement details.

### Phase 3 — MCP Surfaces
- **Deliverables**: MCP server + smoke tests; agent docs for Codex/Cursor.
- **Exit**: Agents can call tools directly; smoke stays green in CI.

### Phase 4 — Remove Node
- **Deliverables**: PR removing `.sentinel/` JS, pnpm files, PowerShell scripts; DECISION entry.
- **Exit**: No Node on path; repo remains green locally and in CI.

### Phase 5 — Linux Hardening
- **Deliverables**: POSIX verification, distro notes, CI Linux badge.
- **Exit**: Identical bootstrap and behavior on Linux/macOS/Windows.

</execution-order>

<risks>
## Technical & Process Risks
- **Spec‑Kit upstream drift**
  - *Mitigation*: Maintain `UPSTREAM.md`; periodic re‑sync task.
- **Validator parity**
  - *Mitigation*: Golden fixtures; JSON output snapshots in tests.
- **Agent UX regressions**
  - *Mitigation*: Gates are additive; emit precise file/line diagnostics; document remediation.
- **Cross‑platform file paths**
  - *Mitigation*: Use `pathlib`, avoid shell‑specific constructs; CI matrix catches drift.
</risks>

<appendix>
## Runbook (local)
```
uv sync
python -m sentinelkit --help
sentinel selfcheck            # runs contract validate + sentinel smoke
pytest -q -m sentinel         # regression suite
```

## Acceptance (what “done” means)
- `specify init --sentinel` produces a repo that, on fresh clone, runs `uv sync && sentinel selfcheck` and passes contracts/context/sentinels/MCP smokes on Windows/Linux/macOS.
- No Node.js, pnpm, or PowerShell anywhere; all CLIs are Python.
- `/speckit.*` commands are transparently gated; failing states block with clear, actionable errors.
- Legacy Node workspace removed; DECISION recorded; CI green.
</appendix>
