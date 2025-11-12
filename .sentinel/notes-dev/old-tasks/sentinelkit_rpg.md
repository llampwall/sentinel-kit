<overview>
## Problem Statement
Multi-agent coding loops fall apart when context grows faster than the repo: PM ⇄ Dev chats accumulate implicit state, specs decay into stale Markdown, and nothing enforces that contracts, tests, docs, and decisions stay in sync. SentinelKit must bolt onto Spec-Kit’s rails to keep agents stateless and memory artifactful—otherwise we reintroduce the same bug every week while drowning in context.

## Target Users
- **Individual founders / tech leads** using Spec-Kit (or Task Master) to orchestrate AI agents and needing guardrails to keep autopilot safe.
- **AI pair-programming workflows** (Codex CLI, Claude Code, Cursor) where a Router hands tasks to specialized agents but lacks enforcement rails.
- **DevOps/QA owners** responsible for contracts/tests/CI wanting machine-readable artifacts (contracts, sentinels, decision ledger) instead of chat logs.

## Success Metrics
- ≥90% of feature branches include a capsule + decision entry + sentinel or contract update before merge.
- Contract validation + sentinel suites run in CI on every PR; failure rate for “reintroduced bug” issues drops below 5% of weekly bugs.
- Router prompts stay <300 lines while achieving 100% of handoffs with explicit RequiredOutputs + context include-lists.
- Task Master parses the PRD into a dependency graph with no cycles; topological execution succeeds (Phase 0→4) without rework.
</overview>

<functional-decomposition>
## Capability Tree

### Capability: Enforcement Primitives
Ensures repos encode memory as artifacts (contracts, sentinels, decisions).

#### Feature: Contract Validation
- **Description**: Validate fixtures against versioned contracts with CLI + MCP surface.
- **Inputs**: `.sentinel/contracts/*.yaml`, `.sentinel/contracts/fixtures/**`.
- **Outputs**: Pass/fail report, validation errors.
- **Behavior**: Walk fixtures, load schema, run AJV (or future Python validator), exit non-zero on failure.

#### Feature: Sentinel Tests
- **Description**: Encode past bugs as tests in `.sentinel/tests/sentinels/**`.
- **Inputs**: Bug reproduction fixtures/code.
- **Outputs**: Deterministic test suites gating regressions.
- **Behavior**: Run targeted suite via CLI/MCP and fail PRs when any sentinel trips.

#### Feature: Decision Ledger & Provenance
- **Description**: Maintain `.sentinel/DECISIONS.md` + file headers linking edits to D-IDs.
- **Inputs**: Decision metadata (author, scope, rationale) from agents.
- **Outputs**: Ledger entry + `ProducedBy=...` headers.
- **Behavior**: CLI/MCP helper appends ledger entry, returns header snippet for agents to paste.

### Capability: Context Capsules & Routing
Keeps agent context bounded and deterministic.

#### Feature: Capsule Template
- **Description**: Spec-side capsule referencing spec/plan/tasks with include-list + acceptance criteria.
- **Inputs**: Feature spec artifacts, allowed context paths.
- **Outputs**: `.specify/specs/<id>/capsule.md`.
- **Behavior**: Generator CLI ensures consistent sections (Goal, Required Outputs, Allowed Context).

#### Feature: Router Prompting
- **Description**: Render router + lead agent prompts with dynamic agent list + mounted context.
- **Inputs**: Capsule file, `.sentinel/agents/**` folders, prompt templates.
- **Outputs**: Router JSON prompt, agent prompt with provenance instructions.
- **Behavior**: `node .sentinel/scripts/orch/prompt-render.mjs` loads templates from `.sentinel/prompts/*.md`, prints the router prompt (`--mode router`), then requires a second invocation (`--mode capsule --agent <id>`) after capturing the router JSON; router decisions are logged outside `DECISIONS.md`. Future work will collapse the two invocations into a single pass.

### Capability: MCP & Tooling
Expose deterministic helpers to Codex/Task Master without bloating context.

#### Feature: `contract-validate` Server (`.sentinel/scripts/mcp/contract-validate-server.mjs`)
- **Description**: MCP server mirroring CLI validation.
- **Inputs**: Contract id or fixture path.
- **Outputs**: JSON validation result.
- **Behavior**: JSON-RPC over stdio, uses the same validator as the CLI; `node .sentinel/scripts/mcp/contract-validate-smoke.mjs` launches the server, runs initialize → tools/list → tools/call, and fails fast if any step regresses.

#### Feature: `sentinel-run` Server (`.sentinel/scripts/mcp/sentinel-run.mjs`)
- **Description**: Runs only sentinel suites and reports failures.
- **Inputs**: None or optional test filter.
- **Outputs**: Pass/fail summary with failing file list.
- **Behavior**: Spawns test runner with sentinel glob; returns structured result.

#### Feature: `decision-log` Server (`.sentinel/scripts/mcp/decision-log.mjs`)
- **Description**: Appends D-entries and emits provenance header snippet.
- **Inputs**: Decision metadata, scope paths.
- **Outputs**: Updated ledger + string snippet (`ProducedBy=...`).
- **Behavior**: Writes to `DECISIONS.md` with NEXT_ID auto-increment.

### Capability: CI & Release Gates
Ensures enforcement scripts run automatically.

#### Feature: CI Gates
- **Description**: GitHub Actions (or equivalent) enforcing contracts, sentinels, docs, decisions.
- **Inputs**: npm/python scripts, repo state.
- **Outputs**: Passing CI badge; failing PRs if gates red.
- **Behavior**: Matrix jobs run validators/tests/doc checks; block merge on failure.
</functional-decomposition>

<structural-decomposition>
## Structural Modules

### Orchestration Flow (Spec-Kit ↔ SentinelKit)
1. **Spec-Kit Lead-Up** *(Phase 1 output)*: Product manager (human or orchestrator agent) runs `/speckit.constitution → /speckit.specify → /speckit.plan → /speckit.tasks`, producing spec/plan/tasks plus a capsule under `.specify/specs/<feature>/capsule.md`.
2. **Capsule Selection** *(Phase 2 dependency)*: When a Task Master task becomes unblocked, the PM copies that capsule path and runs `node .sentinel/scripts/orch/prompt-render.mjs --capsule <capsule> --mode router` (CLI delivered in Phase 2 - Capsules & Routing).
3. **Router Handoff** *(Phase 2 deliverable)*: The Router agent responds with JSON (`leadAgent`, `requiredOutputs`, `contextToMount`, `notes`). Prompt-render logs the JSON to `.sentinel/router_log/<slug>.jsonl`.
4. **Agent Execution** *(Phase 2→Phase 3 bridge)*: The PM (or automation) reruns prompt-render with `--mode capsule --agent <leadAgent>` to produce the working agent prompt. The agent only mounts the capsule's Allowed Context plus `.sentinel/agents/<leadAgent>/**`.
5. **Artifacts Back to Spec-Kit** *(Phase 1/3 enforcement)*: Agent updates contracts/sentinels/docs/DECISIONS as required, then human reviewers feed diffs back through the normal Spec-Kit git/PR flow. Task Master marks the task complete once artifacts + ledger entries are merged.
6. **Dynamic Agent Adds** *(ongoing)*: Dropping new folders under `.sentinel/agents/<id>` (agent.json + ROLE/PLAYBOOK) immediately exposes them to prompt-render; no CLI updates needed unless we want `specify init` to ship them by default. Specialized agents (Integrator, Designer, CapsuleAuthor, etc.) can be added/removed per repo—Router is the only required entry.
7. **CapsuleAuthor Loop** *(optional)*: A dedicated CapsuleAuthor agent can patch capsules (or create new ones) whenever other agents discover plan gaps, enabling closed-loop `/speckit.implement` runs without human intervention. When present, Capsules must log the new decisions and rerun lint/tests automatically.

### Module: `.sentinel/contracts`
- **Responsibility**: Store contracts, fixtures, README, provenance headers.
- **Implementation**: YAML schema files (`<domain>.vN.yaml`) + `fixtures/<domain>/*.json`.
- **Interfaces**: Consumed by CLI, MCP servers, tests.

### Module: `.sentinel/tests`
- **Responsibility**: Sentinel suites (`tests/sentinels/**`) + runner scripts.
- **Implementation**: Vitest (Node) initially; future language adapters allowed.
- **Interfaces**: `npm run test:sentinels`, MCP `sentinel-run`.

### Module: `.sentinel/scripts`
- **Responsibility**: Node utilities (contract validation, MCP servers, prompt renderer).
- **Implementation**: `package.json` scoped to `.sentinel/`, ESM modules.
- **Interfaces**: CLI via `node .sentinel/scripts/...`, MCP via JSON-RPC stdio, smoke harnesses such as `contract-validate-smoke.mjs`.

### Module: `.sentinel/agents`
- **Responsibility**: Role definitions (ROLE/CHECKLIST/PLAYBOOK + agent.json) with RulesHash; holds Router (mandatory) plus optional specialists (Builder, Integrator, Designer, CapsuleAuthor, Scribe, etc.).
- **Interfaces**: Prompt renderer mounts these folders for lead agents; CapsuleAuthor can be invoked to edit capsules when the plan changes mid-run.

### Module: `.sentinel/docs/IMPLEMENTATION.md`
- **Responsibility**: Living runbook describing current enforcement surface, execution flow, stack context, and CI gates.
- **Interfaces**: Updated by `/speckit.plan`, CapsuleAuthor, or CLI helpers whenever architecture/stack decisions change; referenced by README/status docs and optional capsule Router Notes.

### Module: `.sentinel/prompts`
- **Responsibility**: Source templates for router/agent prompts (e.g., `sentinel.router.md`, `sentinel.capsule.md`).
- **Interfaces**: Consumed by `prompt-render` when generating prompts.

### Module: `.sentinel/router_log`
- **Responsibility**: Lightweight handoff log (`.sentinel/router_log/*.jsonl`) capturing router selections for auditing without polluting `DECISIONS.md`.
- **Interfaces**: Written by router/prompt tooling; readable by humans or future dashboards.

### Module: `.specify/` (Spec-Kit)
- **Responsibility**: Constitution, specs, plans, tasks, capsules, scripts.
- **Interfaces**: `specify` CLI commands; capsule generator references these docs.

### Module: Spec-Kit Integration Hooks
- **Responsibility**: Wire SentinelKit assets into Spec Kit's scaffolding so `/speckit.*` commands and release templates stay aware of Sentinel add-ons.
- **Implementation**: `src/specify_cli/__init__.py` (`AGENT_CONFIG` + `--ai` help text), `templates/commands/*.md` (slash-command scaffolds), `.github/workflows/scripts/create-release-packages.sh` / `create-github-release.sh` (agent-specific archives), and `scripts/{bash,powershell}/update-agent-context.*` (agent rules files).
- **Interfaces**: `specify init --ai <agent>` downloads the per-agent archive, release scripts now tolerate missing `agent_templates/*` folders (optional Gemini/Qwen handbooks) via guarded copies, and context updaters refresh `.windsurf/`, `.codex/`, etc. Task Master should own follow-ups whenever SentinelKit needs new agent prompts or optional template bundles.

### Module: `.sentinel/context`
- **Responsibility**: `.sentinel/notes-dev/SentinelKit_thesis.md`, `.sentinel/notes-dev/SentinelKit_salvage_plan.md`, implementation notes.
- **Interfaces**: Linked from README/PRD; capsules may include these files explicitly.
</structural-decomposition>

<dependency-graph>
## Dependency Graph (Topological)

1. **Phase 0 – Groundwork**
   - Clone Spec-Kit, install CLI via `uv`.
   - Port SentinelKit assets into `.sentinel/`, ensure Node toolbelt available.

2. **Phase 1 – Enforcement Primitives**
   - Contracts/fixtures, sentinel test harness, decision ledger + headers.
   - CLI validators running via npm scripts.
   - Depends on Phase 0 (paths + tooling).

3. **Phase 2 – Capsules & Routing**
   - Capsule template referencing spec/plan/tasks.
   - `.sentinel/agents` definitions + prompt renderer pointing at new folders.
   - Depends on Phase 1 (needs ledger, contracts, agent folders).

4. **Phase 3 – MCP Tooling**
   - `contract-validate`, `sentinel-run`, `decision-log` servers.
   - Optional context-linter utility.
   - Depends on Phase 2 (needs stable scripts + capsule paths).

5. **Phase 4 – CI & Release Gates**
   - CI pipelines enforcing contracts/sentinels/docs/decisions.
   - Depends on Phases 1–3 (scripts/tests/MCP) plus CI provider setup.
</dependency-graph>

<execution-order>
## Phase Breakdown & Deliverables

### Phase 0 – Groundwork
- Clone upstream Spec-Kit (done) and document `UPSTREAM.md`.
- Install `specify-cli` from local clone via `uv`.
- Add `.sentinel/package.json` + Node deps; ensure MCP server boots.

### Phase 1 – Enforcement Primitives
- Port contracts/fixtures + sentinel tests; ensure `npm run validate:contracts` & `npm run test:sentinels`.
- Recreate `DECISIONS.md` with NEXT_ID and provenance header guidance.
- Update README/IMPLEMENTATION describing enforcement loop.

### Phase 2 - Capsules & Routing
- Author capsule template consistent with Spec/Plan/Tasks (plus generator CLI if needed).
- Populate `.sentinel/agents/{router,scribe,builder,...}` with ROLE/PLAYBOOK scaffolds (checklist section optional) + RulesHash.
- Refactor/document single-pass `prompt-render.mjs` that emits router prompt → reads JSON → emits lead-agent prompt, logging selections to `.sentinel/router_log/`.
- Add README/PRD “Orchestration Flow” checklist describing how Spec-Kit PMs hand off capsules to the router + lead agent.
- Ensure capsules mount minimal include lists (<300 lines).

### Phase 3 - MCP Tooling
- Maintain `contract-validate` server + smoke test (keep `contract-validate-smoke` green).
- Implement `sentinel-run` + `decision-log` MCP servers; provide CLI fallbacks.
- Add smoke clients/scripts proving each server responds.

### Phase 4 – CI & Release Gates
- Configure CI (GitHub Actions) for contracts, sentinels, docs, decision enforcement.
- Document quickstart + enforcement loop in README + `.sentinel/docs/IMPLEMENTATION.md`.
</execution-order>

<risks>
## Technical Risks
**Risk**: Node + Python mixed stack confuses contributors.  
- **Impact**: Medium (onboarding friction).  
- **Mitigation**: Scope Node tooling to `.sentinel/`, document install steps, consider Python reimplementation later.  
- **Fallback**: Provide Docker/devcontainer script installing both toolchains.

**Risk**: MCP servers fail handshake (current issue).  
- **Impact**: High (tools unusable in Codex).  
- **Mitigation**: Add integration tests that run servers + synthetic initialize calls; log structured JSON only.  
- **Fallback**: Keep CLI equivalents so agents can run scripts manually.

## Dependency Risks
- Upstream Spec-Kit changes may conflict with derivative. *Mitigation*: maintain `UPSTREAM.md` + periodic sync plan.

## Scope Risks
- Capsules drifting into mini-specs again. *Mitigation*: enforce context-budget linter early; Router rejects capsules > limit.
- MCP overbuild before MVP. *Mitigation*: mark MCP features optional in PRD; milestone gating ensures CLI path works first.
</risks>

<appendix>
## References
- `.sentinel/notes-dev/SentinelKit_thesis.md` – Mission, pillars, differentiation.
- `.sentinel/notes-dev/SentinelKit_salvage_plan.md` – Asset inventory + phased plan.
- Spec-Kit upstream repo (`../spec-kit/`) – Base CLI and templates.

## Glossary
- **Capsule**: Context package under `.specify/specs/<id>/capsule.md` with include-list & acceptance criteria.
- **Sentinel**: Regression test capturing a previously-fixed bug.
- **Decision Ledger**: `DECISIONS.md` log + per-file provenance headers.
- **Router**: Agent/prompt that assigns one lead agent and required outputs per capsule.

## Open Questions
1. Should contract validation migrate to Python to match Spec-Kit stack?
2. Do we ship context linter as MCP server or CLI first?
3. How do we standardize RulesHash generation/versioning for agents?
4. Do we eventually publish optional agent template guides (e.g., Gemini/Qwen handbooks) or keep the release script skips permanent?
</appendix>
