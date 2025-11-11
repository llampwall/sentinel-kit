# SentinelKit Salvage Plan

## 1. Objectives
- **Reset foundation on real Spec-Kit rails.** Clone upstream Spec-Kit to create a private derivative repo so SentinelKit can extend the actual commands/slash workflows instead of templated copies.
- **Port working enforcement primitives.** Carry over the minimal but functioning pieces (contracts/fixtures, sentinel test, MCP validator, prompt renderer) as seed artifacts.
- **Keep planning external to SentinelKit.** Use Task Master (or any planner) strictly as a maintainer aid; SentinelKit’s user-facing surface stays Spec-Kit + Sentinel artifacts.
- **Maintain a dependency-aware plan.** Produce an RPG-style PRD for maintainers so any planner (Task Master optional) can parse capabilities, structural modules, and dependencies into a reliable task graph.

## 2. Assets to Preserve From Current Repo
| Asset | Reason to keep | Porting notes |
| --- | --- | --- |
| `.sentinel/contracts/users.v1.yaml` + fixtures | Demonstrates contract format + provenance header pattern | Copy into new repo’s `.sentinel/contracts/` as reference contract |
| `tests/sentinels/sentinel_users_email_format.test.mjs` | Example sentinel + Vitest harness | Port to show sentinel naming & CI expectations |
| `scripts/contracts/validate.mjs` | Baseline contract validator used by npm script | Adapt paths once repo cloned; align with Spec-Kit structure |
| `scripts/mcp/contract-validate-server.mjs` + smoke client | First MCP tool; validates schema | Keep as reference for MCP interface even if re-implemented |
| `scripts/orch/orchestrate.mjs` + prompt templates | Working Router/Lead prompt renderer | Rename when integrating into true orchestrator stack |
| `context/SentinelKit_thesis.md` | Canonical mission + pillars | Becomes appendix/reference in PRD |
| `DECISIONS.md` format + provenance headers | Ledger template & header convention | Keep NEXT_ID + examples to enforce discipline immediately |

## 3. Big Swings We Are NOT Carrying Forward
- Spec work implemented via capsules alone (capsules go back to “context packages,” not spec substitutes).
- PM-produced “Orchestrator” terminology confusion. The CLI helper will be documented as Prompt Renderer; orchestrator roles will be agents defined under `.sentinel/agents/`.
- Half-integrated Task Master references: remove from product surface; Task Master becomes the planning tool, not a user-facing feature.

## 4. Phased Rebuild (Topological Order)
### Phase 0 – Groundwork
1. Clone Spec-Kit upstream repo privately; confirm slash commands run locally.
2. Snapshot current sentinel-kit repo for reference; note commit hash in new repo README appendix.
3. Copy over preserved assets into equivalent folders; fix paths to match new structure.

### Phase 1 – Enforcement Primitives
1. Stand up `.sentinel/` with contracts, fixtures, sentinel tests, decision ledger.
2. Port `scripts/contracts/validate.*` and `npm run` scripts; ensure CI placeholder exists.
3. Recreate provenance header tooling (templates or instructions).

### Phase 2 - Context Capsules & Router Surface
1. Define capsule template aligned with Spec-Kit spec/plan/tasks (capsule references those docs).
2. Install `.sentinel/agents/` with ROUTER, SCRIBE, BUILDER, etc., including ROLE/PLAYBOOK templates (checklists optional) + RulesHash versioning.
3. Refactor prompt renderer into a single-pass `prompt-render` command: it emits the router prompt, captures the router’s JSON, and immediately emits the selected agent prompt (no second manual run); router decisions log to a lightweight `.sentinel/router_log/` instead of `.sentinel/DECISIONS.md`.

### Phase 3 – MCP + Tooling Loop
1. Harden `contract-validate` MCP server; add tests proving Task Master / Codex can call it.
2. Implement `sentinel-run` MCP server (runs `tests/sentinels/**`).
3. Implement `decision-log` MCP helper that appends to `DECISIONS.md` and returns provenance snippet.

### Phase 4 – CI & Release Gates
1. Finalize RPG PRD (internal planning aid) and store in `.taskmaster/docs/sentinelkit_rpg.md` for maintainers; mark as optional dependency.
2. Wire CI (GitHub Actions or equivalent) enforcing contracts + sentinels + docs + decision entries.
3. Document workflow in README + IMPLEMENTATION (quickstart should not require Task Master).

## 5. Dependencies (High Level)
| Task | Depends on |
| --- | --- |
| Phase 1 enforcement | Phase 0 groundwork |
| Capsule template + agent prompts | Phase 1 (needs `.sentinel/` + contracts) |
| MCP servers | Phase 1 (validation scripts) |
| CI gates | Phases 1–3 (needs scripts + tests + MCP optional) |

## 6. Risks & Mitigations
- **Risk:** Forking Spec-Kit introduces upstream drift.  
  **Mitigation:** Maintain a `UPSTREAM.md` noting commit SHA, run periodic merges.
- **Risk:** Task Master PRD too bulky for context.  
  **Mitigation:** Keep thesis separate; PRD references thesis instead of embedding whole text.
- **Risk:** MCP tooling overkill for MVP.  
  **Mitigation:** Keep CLI equivalents (`npm run validate:contracts`, `npm run test:sentinels`) so repo is usable without MCP; MCP servers labeled optional.
- **Risk:** Capsule/include-list discipline erodes again.  
  **Mitigation:** Build “context linter” early (Phase 2 subtask) to warn when include-lists exceed budget.

## 7. Deliverables for Next Repo Commit
1. `.sentinel/notes-dev/SentinelKit_thesis.md` (already written; import verbatim).
2. `.sentinel/notes-dev/SentinelKit_salvage_plan.md` (this document).
3. `docs/UPSTREAM.md` stub referencing Spec-Kit clone target (to be completed during Phase 0).
4. `PRD` skeleton based on RPG template (next step).

This plan feeds directly into the RPG PRD: the phases map to dependency layers, assets inform the “Structural Decomposition,” and risks feed the PRD risk section.
