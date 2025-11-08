# SentinelKit Thesis

## Mission
Deliver a lightweight, vendor-agnostic enforcement layer that makes AI coding agents **stateless** while keeping a project’s memory **artifactful**. SentinelKit bolts onto Spec-Kit (or any spec-first workflow) so features ship fast without re‑introducing old bugs or inflating context windows.

## The Problem We Are Solving
1. **Chat drift & lost-in-the-middle.** Long-running PM ⇄ Dev conversations accumulate implicit state that new agents can’t recover.
2. **Spec decay.** Specs live in Markdown, but implementation decisions and regressions aren’t fed back into durable artifacts, so the same bug reappears.
3. **Context bloat.** Agents are handed whole repos; they hallucinate or overwrite unrelated files because nothing constrains what they’re allowed to read.
4. **Enforcement vacuum.** Even when teams write specs, nothing forces contracts/tests/docs/provenance to stay in sync. “Looks good” reviews let regressions slip.

## Core Response
SentinelKit constrains *context* and amplifies *artifacts*. Every task runs inside a tiny **capsule** (include-list + acceptance) and must emit audit-ready artifacts: contracts/fixtures, sentinel tests, decision ledger entries, provenance headers, and updated docs. The repo’s longitudinal memory is the combination of those artifacts—not chat logs or human recollection.

## Pillars
1. **Stateless agents, artifactful memory.** Agents reboot fresh every task; only contracts/fixtures/sentinels/decisions persist.
2. **Contracts-first, versioned boundaries.** Every interface lives in `.sentinel/contracts/<domain>.vN.(yaml|json)` with fixtures. Breaking change ⇒ version bump; consumers must pass validation before merge.
3. **Sentinel tests encode past bugs.** Every bug fix adds `tests/sentinels/sentinel_<slug>.*`. CI blocks merges if any sentinel fails.
4. **Decision ledger + provenance crumbs.** `DECISIONS.md` logs D-#### entries. Each touched file starts with `ProducedBy=<Agent> RulesHash=<role>@<ver> Decision=<ID>`.
5. **Capsules as context packages.** `.specify/specs/<id>/capsule.md` enumerates Goal, Required Outputs, Acceptance Criteria, and an **Allowed Context** include-list. Agents may only open those paths.
6. **Router ownership & gated handoffs.** A Router agent picks exactly one Lead Agent and enumerates deliverables + mounted context. Handoffs aren’t vibes; they’re contracts.
7. **Observability & release gates baked in.** Structured logs, coverage, contract validation, sentinel suites, doc updates, and decision entries are required to merge.
8. **Vendor-neutral MCP tooling.** Optional micro-servers (`contract-validate`, `sentinel-run`, `decision-log`) expose deterministic helpers every agent can call.

## Differentiation From Adjacent Systems
| System | What it provides | What SentinelKit adds |
| --- | --- | --- |
| **Spec-Kit** | Constitution/spec/plan/tasks rails, slash-command UX | Enforced artifacts (contracts, sentinels, decisions), capsules, router prompts, MCP tooling |
| **BMAD** | Artifact-as-memory narrative “story files” | Versioned contracts + fixtures, decision ledger, rules-hash provenance, CI gates |
| **Task Master** | Backlog/PRD management via MCP | Enforcement of outputs; Task Master can own planning while SentinelKit guards execution |
| **Claude Skills / Skills folders** | Vendor-specific modular context | Repo-native capsules with explicit include lists, cross-agent rules |

## Non-Goals
- Replace Spec-Kit’s rails or Task Master’s backlog; SentinelKit is additive.
- Build a monolithic orchestrator agent. Routing stays simple and explicable.
- Support domain agents (e.g., “NFL Schedule Agent”). Every agent here serves the software lifecycle only.
- Maintain long-lived agent memory. If state belongs somewhere, it becomes an artifact.

## Operating Model
1. Product work begins with Spec-Kit (or Task Master) authoring a spec/plan/tasks set.
2. Each feature gets a capsule that links to those files but trims context to the smallest viable include-list.
3. Router prompt (rendered via CLI/script) loads the capsule, lists available agents, and outputs JSON with leadAgent, requiredOutputs, acceptanceCriteria, contextToMount.
4. The chosen agent’s prompt mounts only the allowed context + that agent’s ROLE/CHECKLIST/PLAYBOOK folder. Deliverables must include diffs, provenance headers, decision IDs, and a verification plan.
5. CI (or local scripts) validates contracts, runs sentinels, and ensures docs + decision ledger updated.

## Required Artifacts Per Change
| Artifact | Purpose |
| --- | --- |
| Contract + fixtures | Defines interface expectations and reusable fixtures |
| Sentinel test | Encodes the bug/edge fixed so it never regresses silently |
| Decision ledger entry | Documents the “why” with an ID referenced in code headers |
| Provenance headers | Per-file breadcrumbs tying edits to agents/rules/decisions |
| Capsule updates | Keeps include-list scoped and acceptance criteria current |
| Implementation notes | `context/IMPLEMENTATION.md` or similar stays accurate |

## Guardrails
- **Context Budget.** Capsules should stay ≤300 lines; exceeding that triggers a split (new capsule/spec).
- **One owner per task.** Router never assigns multiple lead agents; collaboration happens via artifacts.
- **RulesHash discipline.** Agent ROLE/CHECKLIST/PLAYBOOK versions are hashed; outputs echo the hash so drift is obvious.
- **No silent contract rewrites.** Old versions remain until all consumers migrate; ledger entries document bumps.
- **CI Gatekeeping.** Merges blocked unless contracts validate, sentinels pass, docs + decisions updated, and lint/tests green.

## “Why now”
Multi-agent coding is accelerating, but without artifact guardrails teams either drown in context or reintroduce bugs weekly. SentinelKit captures the lessons from running PM ⇄ Codex loops manually: keep agents stateless, push everything you learn into durable artifacts, and make prompts deterministic. By codifying that discipline (and keeping it vendor-neutral), SentinelKit becomes a portable safety layer any AI-assisted team can drop onto their repo.

