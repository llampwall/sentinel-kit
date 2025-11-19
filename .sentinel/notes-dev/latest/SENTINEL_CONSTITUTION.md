# Sentinel-Kit Constitution

This document sets the non‑negotiable rules for Sentinel‑Kit as an opinionated enforcement and agentic layer on top of GitHub Spec‑Kit. It is binding on maintainers, contributors, and agent workflows that claim to run “with Sentinel.”

Sentinel‑Kit does not replace Spec‑Kit. It rides on the same rails—**constitution → spec → plan → tasks → implement**—and adds capsules, agents, and enforcement on top.

---

## 1. Relationship to Spec‑Kit

1.1 **Bolt‑on, not a fork.** Sentinel‑Kit must remain a bolt‑on to Spec‑Kit. A project initialized with `specify init <NAME> --sentinel`:

- Uses the standard `/speckit.*` flow (`/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`).
- Does not require additional top‑level commands or manual wiring for the end user.

1.2 **Spec layers stay distinct.** Sentinel‑Kit must preserve Spec‑Kit’s artifact boundaries:

- **Constitution** – non‑negotiable principles and constraints for the repo.
- **Spec** – product‑level WHAT and WHY.
- **Plan** – technical HOW (architecture, stack, libraries, interfaces).
- **Tasks** – implementation breakdown derived from the plan.

Sentinel‑specific files (`.sentinel/**`, agent definitions, sentinel tests, decision ledger) may reference or generate these artifacts, but must not blur their responsibilities.

1.3 **No new Spec-Kit slash-command rails.** End users should not need additional top-level project verbs beyond /speckit.* and the uv run sentinel … CLI.

- Scaffolded assets under `.sentinel/**` and `sentinelkit/`.
- Capsule templates and context rules.
- Agent prompts wired into IDEs / CLIs.
- MCP tools exposed to agents.

Feature work remains anchored in `/speckit.*` and `uv run sentinel …`, not in extra bespoke CLIs.

1.4 **Backwards‑compatible by default.** Sentinel‑Kit must not break vanilla Spec‑Kit usage unless the change is:

- Explicitly versioned and documented, and
- Guarded by feature flags or templates that clearly opt into Sentinel behavior.

Existing Spec‑Kit projects should be able to adopt Sentinel incrementally without rewriting their entire workflow.

---

## 2. Capsules and Context

2.1 **Capsule‑first work.** Any non‑trivial unit of work must run under a capsule file in `.specify/specs/<id>/capsule.md` that declares:

- Goal and Acceptance Criteria.
- Allowed Context paths (tight include lists).
- Required Outputs and their locations.

Ad‑hoc “just edit the repo” loops are discouraged; Sentinel’s happy path is capsule‑driven.

2.2 **Allowed Context is a hard boundary.** Agents and tools must treat `Allowed Context` as a strict whitelist:

- Reads are limited to the paths listed in the capsule (plus explicitly allowed shared assets such as `.sentinel/docs/**`).
- Reading or depending on files outside Allowed Context is a violation and must be treated as a bug in the capsule or the agent.

2.3 **Small, composable capsules.** Capsules should favor:

- Single‑responsibility changes with clear acceptance criteria.
- Explicit handoffs between capsules rather than “kitchen sink” specs.

If a capsule begins to rely on broad repo access or ambiguous goals, the correct response is to split it into smaller capsules, not to relax context boundaries.

2.4 **Capsule metadata is source of truth.** For agent runs, the capsule’s Goal, Acceptance, Allowed Context, and Required Outputs override ad‑hoc instructions in chat. Human authors may adjust capsules, but agents must not silently override capsule constraints.

---

## 3. Agents and Roles

3.1 **Router is mandatory.** Every capsule run must have a **Router** agent that:

- Selects a single lead agent for the capsule.
- Declares the mounted context and Required Outputs for that agent.
- Decides when to stop, escalate, or spawn follow‑up capsules.

No other agent may self‑appoint as capsule lead without Router selection.

3.2 **Roles are strict scopes.** Each agent under `.sentinel/agents/**` has:

- `ROLE.md` – mission, in‑scope/out‑of‑scope work, required outputs, quality bar, escalation rules.
- `PLAYBOOK.md` – step‑by‑step behavior for running a capsule.

Agents must:

- Stay within their ROLE’s declared scope.
- Produce the required outputs and headers (e.g., ProducedBy, RulesHash, Decision, Related‑Capsule).
- Escalate for new capsules or Router decisions when work falls outside their remit.

3.3 **Stateless agents, stateful artifacts.** Agent memory is not trusted across sessions. Durable knowledge must live in artifacts:

- Specs, capsules, contracts, context limits.
- Sentinel tests and their results.
- Decision ledger entries (`.sentinel/DECISIONS.md`).

Agents must re‑ground themselves from artifacts rather than relying on prior chat history.

3.4 **Pluggable, not bespoke, roles.** New roles (e.g., Designer, Refactorer, Releaser) must be defined via ROLE/PLAYBOOK under `.sentinel/agents/**` and wired into Router logic; they may not be introduced as one‑off prompt hacks.

---

## 4. Sentinel Enforcement and Provenance

4.1 **External referee, not vibes.** Sentinel‑Kit’s purpose is to move judgment out of the model and into deterministic checks:

- Contracts + fixtures define API and data boundaries.
- Sentinel tests encode regressions and critical behaviors.
- Context lint/budgets enforce bounded reading.
- Decision ledger and provenance headers track “why” changes exist.

Agents and humans must treat these artifacts as the referee for “is this acceptable?”

4.2 **Gates before “done.”** In a sentinel‑enabled project, non‑trivial changes are not “done” until:

- Contracts validate for affected fixtures.
- Sentinel tests relevant to the change pass.
- Context lint passes for the capsule’s Allowed Context.

These gates must be callable both via CLI (`uv run sentinel …`) and via MCP tools inside agents.

4.3 **Decision ledger for meaningful trade‑offs.** Substantive architectural decisions, risk trade‑offs, and non‑obvious compromises must be recorded via the decision ledger:

- Entries live in `.sentinel/DECISIONS.md` with ProducedBy, RulesHash, Decision, and Related‑Capsule metadata.
- Agents use the `sentinel_decision_log` MCP tool (or `sentinel decisions append`) for structured updates.

Silent, undocumented “cleverness” is treated as a defect in governance.

4.4 **ProducedBy and provenance headers.** Sentinel‑managed artifacts (capsules, decision ledger entries, snippets, some docs) must carry provenance headers that identify:

- Producing agent or role.
- Ruleset / hash used for the decision.
- Capsule or spec the change relates to.

Maintainers must not strip or falsify these headers; evolving the schema is allowed but must be done deliberately.

4.5 **Vendor‑agnostic enforcement.** Sentinel‑Kit’s contracts, tests, and provenance rules must not depend on a particular LLM provider. MCP tooling and CLI behavior must work across Codex, Claude Code, Cursor, and other MCP‑capable clients so long as they respect the protocol.

---

## 5. CLI, MCP, and UX Principles

5.1 **Single source of truth for behavior.** The Sentinel CLI (`uv run sentinel …`) and the MCP tools exposed by `sentinel mcp server` must reflect the same semantics. Any gate or behavior implemented in one must be reachable via the other.

5.2 **Smooth Spec‑Kit integration.** The recommended flow for users is:

1. Scaffold with `specify init <NAME> --sentinel`.
2. Run `specify check` and `uv run sentinel selfcheck`.
3. Use `/speckit.*` commands to evolve specs and plans.
4. Let agents call Sentinel’s MCP tools between steps to decide whether to continue.

Sentinel‑specific complexity (contracts, capsules, agents) is surfaced through scaffolded structure and auto‑wired MCP, not extra manual configuration.

5.3 **Repo dogfooding.** This repository must dogfood Sentinel‑Kit:

– Local development and CI must run uv run sentinel selfcheck and sentinel tests.
– Changes to Sentinel-Kit must maintain contracts, capsules, and decision ledger entries.
– Whether planning is done with Spec-Kit, Task-Master, or something else is an implementation detail.

5.4 **Minimal friction defaults.** Defaults for new users must emphasize:

- Clear quickstarts (`specify init --sentinel`, `uv run sentinel selfcheck`).
- Pre‑configured MCP entries for common agents (e.g., Codex) where possible.

Expert users can customize, but defaults must be safe and predictable.

---

## 6. Scope and Evolution

6.1 **v1 scope.** Sentinel‑Kit v1 is scoped to:

- Single‑repo projects built on Spec‑Kit.
- Capsule‑based task execution with a small core of agents (Router, Builder, Verifier, Scribe, etc.).
- Enforcement via contracts, sentinel tests, context linting, and MCP tools.

6.2 **Out‑of‑scope for v1.** The following are explicitly out of scope and require separate specs before implementation:

- Multi‑repo orchestration and cross‑repo capsules.
- Large agent swarms or orchestration fabrics beyond Router‑centric flows.
- UI dashboards, portals, or visualization layers.

Exploration is allowed in branches or experiments, but landing in `main` requires dedicated specs and updated sentinel artifacts.

6.3 **Compatibility guarantees.** Sentinel‑Kit must track upstream Spec‑Kit releases and preserve a clear migration path:

- Template changes that materially alter behavior must be versioned and documented.
- MCP schema and tool behavior changes must preserve compatibility or ship with adapters and/or clear breaking‑change notes.

---

## 7. Responsibilities of Maintainers and Agents

7.1 **Maintainers must:**

- Keep the scaffolded assets (`src/sentinel_assets/**`) in sync with the library code (`sentinelkit/**`) so new projects inherit correct behavior.
- Treat sentinel failures in CI as blocking for releases, except where explicitly documented as “allowed pending” with an associated decision ledger entry.
- Update this constitution when core principles change, and ensure downstream docs (README, prompts, capsules) reflect the new rules.

7.2 **Agents (and humans acting as agents) must:**

- Honor capsule Allowed Context boundaries.
- Follow ROLE/PLAYBOOK guidance for the agent they are running.
- Use Sentinel tools (CLI or MCP) to validate work before declaring it complete.
- Record meaningful decisions in the ledger instead of burying them in chat.

7.3 **Constitution changes are gated.** Edits to this document must be:

- Driven by a dedicated capsule and spec that describe the change.
- Accompanied by appropriate updates to prompts, sentinel tests, and (when relevant) contracts.
- Recorded in the decision ledger with a clear rationale and scope.

Once accepted, these rules govern future work on Sentinel‑Kit until superseded by another explicit constitutional change.

