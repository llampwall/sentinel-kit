# Specification‑Driven Development, Enforced by SentinelKit

> A unified thesis for shipping with speed **and** discipline: specifications generate the code; SentinelKit guarantees the artifacts that keep the system honest.

---

## 1) The Power Inversion
For decades, teams treated specifications as scaffolding and code as the truth. Specification‑Driven Development (SDD) flips that hierarchy: **code serves the specification**. PRDs and implementation plans are not disposable prose; they are **executable** inputs that generate working systems. Maintaining software means evolving the specification and its implementation plan; code is the last mile expression of intent.

## 2) The SDD Workflow in Practice
SDD starts from a rough idea and iteratively hardens it into a complete PRD with acceptance criteria. Research agents gather constraints; the plan translates requirements into architecture; tasks are derived mechanically. The output is a living set of artifacts—specs, plans, contracts, data models, quickstarts, and tests—versioned in a feature branch. Implementation regenerates from those artifacts whenever intent changes.

### Command Rails (Spec‑Kit)
Spec‑Kit operationalizes SDD via a narrow set of slash commands:
- **`/speckit.specify`** → creates a numbered feature spec, branch, and folder.
- **`/speckit.plan`** → produces an implementation plan, data models, contracts, research, and a quickstart.
- **`/speckit.tasks`** → derives an executable `tasks.md` with parallelization hints.
These commands keep the documentation, plans, and generated outputs aligned and traceable.

---

## 3) Why SDD Needs an Enforcement Layer
Pure SDD still leaves gaps in practice:
- Chat threads accumulate fragile, implicit state
- Specs decay unless changes are forced back into artifacts
- Agents over‑read repos and hallucinate edits
- Reviews bless regressions because nothing gates contracts/tests/docs/provenance

Enter **SentinelKit**.

## 4) SentinelKit: Mission and Posture
**Mission:** provide a lightweight, vendor‑agnostic enforcement layer that makes coding agents **stateless** and project memory **artifactful**. SentinelKit bolts onto Spec‑Kit (or any spec‑first workflow) without replacing its rails.

### Core Response
Constrain **context** and amplify **artifacts**. Every task executes inside a small **capsule** (explicit include‑list + acceptance) and must emit audit‑ready artifacts. The longitudinal memory of the project is the set of these artifacts—not chat history.

### Pillars
1. **Stateless agents, artifactful memory.** Agents reboot each task; only contracts/fixtures/sentinels/decisions persist.
2. **Contracts‑first, versioned boundaries.** Interfaces live in `.sentinel/contracts/<domain>.vN.*` with fixtures; breaking changes require a version bump and validation.
3. **Sentinel tests encode past bugs.** Every bug fix adds a focused test under `tests/sentinels/**`; CI blocks merges when any sentinel fails.
4. **Decision ledger + provenance headers.** `DECISIONS.md` logs D‑IDs; touched files include `ProducedBy=… RulesHash=… Decision=…` headers.
5. **Capsules as context packages.** Each feature’s capsule (`.specify/specs/<id>/capsule.md`) lists Goal, Required Outputs, Acceptance Criteria, and **Allowed Context**. Agents may only read those paths.
6. **Router ownership & gated handoffs.** A Router selects a single lead agent and enumerates deliverables and mounted context.
7. **Observability & release gates.** Contract validation, sentinel suites, doc updates, and decision entries are mandatory to merge.
8. **Vendor‑neutral MCP tooling.** Optional `contract-validate`, `sentinel-run`, and `decision-log` servers expose deterministic helpers to any agent.

---

## 5) Orchestration: Spec‑Kit × SentinelKit
The rails stay Spec‑Kit; SentinelKit supplies guardrails.

**Flow**
1. Use Spec‑Kit to produce `spec.md`, `plan.md`, and `tasks.md` for a feature.
2. Create a **capsule** that references those artifacts and enumerates **Allowed Context** (keep it under ~300 lines).
3. Run the **Router** prompt renderer to list candidate agents and output JSON (`leadAgent`, `requiredOutputs`, `acceptanceCriteria`, `contextToMount`).
4. Render the **lead agent** prompt with only the capsule’s paths plus the agent’s ROLE/CHECKLIST/PLAYBOOK; execute tasks.
5. On completion, changes must include diffs, **provenance headers**, a **decision‑ledger entry**, and a **verification plan**. CI validates contracts, runs sentinels, and checks docs before merge.

**Where SDD Commands Fit**
- `/speckit.specify` and `/speckit.plan` produce the inputs that capsules reference.
- `/speckit.tasks` informs the Router and lead agent deliverables.
- Capsule creation can be scripted (generator optional) but remains transparently textual and reviewable.

---

## 6) Required Artifacts Per Change
| Artifact | Purpose |
|---|---|
| **Contract + fixtures** | Define and validate interface expectations |
| **Sentinel test** | Capture the regression/edge condition permanently |
| **Decision ledger entry** | Document the “why”; supply ID for provenance headers |
| **Provenance headers** | Per‑file breadcrumbs tying edits to agents/rules/decisions |
| **Capsule updates** | Keep include‑lists minimal and acceptance criteria current |
| **Implementation notes** | Keep `IMPLEMENTATION.md`‑style context accurate |

---

## 7) Guardrails
- **Context Budget:** capsules ≤ ~300 lines; split when larger.
- **Single Ownership:** one lead agent per task; collaboration happens via artifacts and handoffs, not shared state.
- **RulesHash Discipline:** agent ROLE/CHECKLIST/PLAYBOOK versions are hashed; outputs echo the hash.
- **No Silent Contract Rewrites:** version contracts; migrate consumers deliberately; ledger entries document bumps.
- **CI Gatekeeping:** merges blocked unless contracts validate, sentinels pass, docs and decisions are updated, and tests are green.

---

## 8) Why Now
AI can generate from precise specifications, but without artifact guardrails teams drown in context and re‑introduce bugs. SDD gives us executable intent; SentinelKit ensures the resulting artifacts stay coherent across time, agents, and branches.

---

## 9) Implementation Surfaces
- **CLI & Scripts** (repo‑native): contract validator, sentinel runner, decision‑log append, prompt renderer.
- **MCP Servers** (optional): stdio JSON‑RPC services for the same helpers.
- **CI Gates**: contracts, sentinels, docs, decision enforcement, plus optional context‑linter.

---

## 10) Glossary
- **SDD** — Specification‑Driven Development.
- **Capsule** — Context package with include‑list + acceptance.
- **Sentinel** — Regression test for a past bug.
- **Decision Ledger** — `DECISIONS.md` entries and per‑file headers.
- **Router** — Agent/prompt that assigns a single lead agent and deliverables for a capsule.

---

## 11) Practical Adoption Notes
- Keep Spec‑Kit’s `/speckit.*` commands as the public interface for product work; introduce SentinelKit artifacts incrementally.
- Start with one contract + fixture pair and one sentinel test; wire CI to fail fast.
- Add capsules only when a feature moves to implementation; keep them tiny.
- Enforce decision logging from the first PR to build provenance muscle.

*This merged thesis is intentionally concise: SDD describes **what** and **why**; SentinelKit enforces **how we keep it true** in code, tests, and history.*

