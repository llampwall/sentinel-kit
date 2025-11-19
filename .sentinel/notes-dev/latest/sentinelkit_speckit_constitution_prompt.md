Create a constitution for Sentinel-Kit, an opinionated extension of GitHub Spec Kit that adds an enforcement and agentic layer on top of spec-driven development.

Sentinel-Kit is NOT a replacement for Spec-Kit. It keeps Spec-Kit’s rails (constitution → spec → plan → tasks → implement), but adds three layers:

1) Capsules: per-feature context packages with Goal, Acceptance, Allowed Context, and Required Outputs.
2) Agents: task-specific roles (Router, Builder, Frontender, Backender, CapsuleAuthor, Verifier, Scribe, etc) each defined by ROLE and PLAYBOOK docs under .sentinel/agents/**.
3) Sentinel enforcement: contracts, fixtures, sentinel tests, decision ledger, and context budgets, exposed via both CLI and an MCP server.

The constitution should define non-negotiable rules for:

**Spec-Kit integration**

* Sentinel-Kit must remain a bolt-on to Spec-Kit, not a forked universe. A project initialized with `specify init <NAME> --sentinel` must follow the standard Spec-Kit flow (`/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`) without extra steps for the end user.
* End users should not have to learn new top-level commands. Sentinel behavior is wired into templates, capsules, agents, and MCP tools behind the scenes.
* Documentation MUST keep a clear separation between:
  - Constitution: non-negotiable project principles.
  - Spec: WHAT and WHY from a product perspective.
  - Plan: technical HOW (stack, architecture, libraries).
  - Tasks: breakdown of work aligned to the plan.

**Capsules and context**

* Every non-trivial unit of work runs under a capsule (`.specify/specs/<id>/capsule.md`) that defines:
  - Goal and Acceptance Criteria.
  - Allowed Context paths (tight include lists).
  - Required Outputs.
* Agents MUST treat Allowed Context as a hard boundary. No reading arbitrary files outside the capsule’s allowed list.
* Capsule design should bias toward small, composable work units with explicit handoffs rather than giant “kitchen sink” features.

**Agents and roles**

* Each agent’s ROLE.md defines mission, in-scope/out-of-scope work, required outputs, quality bar, and escalation triggers. PLAYBOOK.md defines step-by-step behavior per capsule.
* Router is required. Its job is to:
  - Select a single lead agent per capsule.
  - Declare required outputs and mounted context for that agent.
* All other agents (Builder, Frontender, Backender, Designer, CapsuleAuthor, Verifier, Integrator, Refactorer, Scribe, Observer, Releaser, Commander, etc.) are pluggable but must:
  - Stay within their ROLE’s scope.
  - Produce the required outputs and headers.
  - Escalate or request follow-up capsules instead of improvising outside their remit.
* Agents are stateless across tasks. Durable memory lives in artifacts (specs, capsules, contracts, sentinel tests, decision logs), not in chat history.

**Sentinel enforcement and provenance**

* Sentinel-Kit provides a vendor-agnostic enforcement layer:
  - Contracts and fixtures define API boundaries.
  - Sentinel tests encode regressions and critical behaviors.
  - Context lint/budgets prevent “read the whole repo” behavior.
  - A decision ledger (`.sentinel/DECISIONS.md`) and provenance headers (ProducedBy, RulesHash, Decision, Related-Capsule) track why changes exist.
* Sentinel CLI and MCP tools (e.g., contract validation and sentinel test runners) are the primary quality gates:
  - For a sentinel-enabled project, non-trivial changes are not “done” until contracts validate and sentinel tests pass.
  - These gates should be usable both from the shell and via MCP tools inside coding agents.

**UX and integration principles**

* Sentinel-Kit must be vendor-agnostic and work with multiple IDE/agent environments that support slash commands and/or MCP (Codex, Copilot, Claude Code, Cursor, etc.).
* The happy path for end users mirrors Spec-Kit’s README examples. Sentinel-specific behavior is mostly visible as:
  - Extra structure in the scaffold (`.sentinel/**`, agent definitions, sentinel tests).
  - Additional tasks and checklists around contracts/tests/provenance.
  - MCP tools available in their IDE.
* The repo’s own development MUST dogfood Sentinel-Kit:
  - Sentinel-Kit itself is maintained with Spec-Kit commands, capsules, agents, and sentinel gates.
  - Any breaking change to the framework must update its own contracts, sentinel tests, and decision ledger entries.

**Scope and evolution**

* Sentinel-Kit v1 focuses on:
  - Single-repo, Spec-Kit–based projects.
  - Capsule-based task execution with Router + a small core of agents.
  - Contract and sentinel-test enforcement via CLI and MCP.
* Multi-repo orchestration, distributed agent swarms, or UI dashboards are explicitly out of scope for v1 and must be treated as separate future specs.
* Backwards-compatibility with vanilla Spec-Kit templates and flows is a priority. Sentinel-Kit may extend templates but should not break standard Spec-Kit usage unless clearly versioned and documented.

Write the constitution as a concise, opinionated set of rules future maintainers and agents must respect. Do not drift into detailed API design; keep this at the principles-and-guardrails level.
