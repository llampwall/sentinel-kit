Write a functional specification for Sentinel-Kit, a layer on top of GitHub Spec Kit that adds capsules, task-specific agents, and an enforcement layer (contracts + sentinel tests + MCP tools) to spec-driven development.

**Goal:**
Make projects created with `specify init <NAME> --sentinel` behave like normal Spec-Kit projects from the end-user’s perspective, while adding:
- Capsule-based task execution.
- A router + task-specific agents with clear roles and playbooks.
- Sentinel enforcement via contracts, sentinel tests, and decision ledger.
- An MCP server that exposes Sentinel tools to AI coding agents.

End users should primarily think “I’m using Spec-Kit,” but get stronger guardrails, provenance, and automated gates “for free.”

**Primary personas:**

* Spec-Kit users who want to reduce drift and vibe-coding when using AI coding agents.
* AI coding agents (Codex, Copilot, Claude Code, Cursor, etc.) executing `/speckit.*` commands.
* Project maintainers who care about contracts, tests, and reproducibility across long-lived projects.

**High-level capabilities to cover in the spec:**

1) **Project scaffolding & CLI integration**

* For `specify init <NAME> --sentinel`, scaffold additional assets alongside the standard Spec-Kit files:
  - `.sentinel/**` directory containing:
    - `agents/**` (ROLE, PLAYBOOK, agent.json for Router, Builder, Frontender, Backender, Designer, CapsuleAuthor, Verifier, Integrator, Refactorer, Scribe, Observer, Releaser, Commander, etc.).
    - default sentinel tests under `.sentinel/tests/sentinels/**`.
    - contracts/fixtures directory for API/data contracts.
    - DECISIONS.md and templates for provenance headers.
    - optional context lint / budget config.
  - `sentinelkit/` Python package (or equivalent) wired into the project environment.
* `specify check` should continue to behave like Spec-Kit’s `specify check`, with any Sentinel-specific checks added in a way that doesn’t break existing workflows.

2) **Capsules as task containers**

* Define how Sentinel-Kit expects capsules (`.specify/specs/<id>/capsule.md`) to be structured:
  - Goal, Acceptance Criteria, Allowed Context paths, Required Outputs, provenance metadata.
* Sentinel-Kit should not replace Spec-Kit’s spec/plan/tasks, but should:
  - Ensure non-trivial work is always tied to a capsule.
  - Provide templates and helpers for CapsuleAuthor to create and update capsules.
* Router and agents must treat Allowed Context as a hard constraint; the spec should describe this behavior at a functional level.

3) **Agent framework (Router + task-specific agents)**

* Sentinel-Kit must support discovering agents dynamically from `.sentinel/agents/**` via `agent.json` files, without hard-coding agent names in the core.
* `agent.json` defines:
  - id, name, rulesHash, summary.
  - routing_keywords used by Router.
  - mount_paths that define what parts of the repo can be mounted into an agent’s context.
  - prompt_files (ROLE.md and PLAYBOOK.md) that describe behavior.
* The Router agent:
  - Reads a capsule and selects a single lead agent.
  - Declares mounted context and required outputs for that agent.
* Other agents:
  - Follow their ROLE/PLAYBOOK contracts (for example: Designer writes tokens and UX specs; Backender implements backend endpoints; Verifier owns tests and contracts; CapsuleAuthor crafts capsules; Scribe updates docs; Releaser handles release steps).
* The spec should describe how these agents are intended to be invoked within `/speckit.implement` (conceptually), without binding to a specific IDE integration.

4) **Sentinel enforcement: contracts, tests, and decision ledger**

* Sentinel-Kit must provide:
  - A contracts layer (schemas + fixtures) for HTTP APIs, data models, and external dependencies.
  - Sentinel tests (e.g., pytest-based) that encode regression tests and critical behaviors, under `.sentinel/tests/sentinels/**`.
  - A decision ledger (`.sentinel/DECISIONS.md`) plus a standard format for provenance headers (e.g., ProducedBy, RulesHash, Decision, Related-Capsule) to be embedded in files created or modified by agents.
* The spec should describe:
  - How contracts and sentinel tests are expected to be updated when new features or breaking changes are introduced.
  - How Sentinel-Kit expects these checks to be integrated into CI or local workflows (at a behavioral level, not CI syntax).

5) **MCP server and tools for coding agents**

* Sentinel-Kit must expose an MCP server process (for example, `uv run sentinel mcp server`) that can be registered in the user’s IDE/agent.
* The MCP server should offer tools such as:
  - `sentinel_contract_validate` – validate contracts/fixtures.
  - `sentinel_sentinel_run` – run sentinel tests.
  - `sentinel_decision_log` – append decision entries and return headers to embed.
  - Optional: `sentinel_mcp_smoke` to verify MCP connectivity.
* The spec should define:
  - Expected inputs/outputs at a high level (arguments, result semantics).
  - How these tools are intended to be used by `/speckit.implement` flows (e.g., agents calling them as gating steps before declaring tasks complete).

6) **Template integration with Spec-Kit phases**

* For projects initialized with `--sentinel`, Spec-Kit templates (for plan, tasks, implement) should be extended so that:
  - Plans describe Sentinel’s role in quality and agent behavior (contracts, sentinels, decision ledger).
  - Generated tasks include explicit steps for:
    - updating contracts/fixtures,
    - writing or updating sentinel tests,
    - running Sentinel checks (either via CLI or MCP),
    - stamping provenance headers.
  - Implementation prompts instruct coding agents to:
    - Use capsules + Router + task-specific agents.
    - Call Sentinel MCP tools as part of “definition of done”.

7) **Non-functional requirements**

* Vendor-agnostic: must work with multiple AI coding environments that support slash commands and/or MCP, without requiring proprietary features.
* Minimal setup overhead for end users compared to vanilla Spec-Kit:
  - Installing Sentinel-Kit should be as simple as pointing `uv tool install specify-cli` at the Sentinel-Kit repo.
  - The primary behavioral difference for users is the presence of `.sentinel/**` and the availability of Sentinel MCP tools.
* Reasonable performance and context usage:
  - Agent ROLE/PLAYBOOK and capsules should be designed to fit within typical context limits for modern code models.
  - Sentinel tests and contracts should be incremental and composable, not monolithic.

**Out of scope for this spec (future specs):**

* Multi-repo orchestration or cross-repo contracts.
* Web dashboards or UIs for visualizing capsules, agents, and decisions.
* Long-running autonomous agents that plan entire multi-month roadmaps without human oversight.
* Tight coupling to any single LLM provider or IDE.

**What I want in this spec:**

* A clear narrative of Sentinel-Kit’s role on top of Spec-Kit and how the three layers (specs, agents, enforcement) interact.
* Feature breakdown by area:
  - Scaffolding/CLI,
  - Capsules,
  - Agents,
  - Enforcement (contracts/tests/ledger),
  - MCP integration,
  - Template integration with plan/tasks/implement.
* Primary user flows:
  - “Initialize a new project with `specify init --sentinel` and run through constitution/spec/plan/tasks/implement.”
  - “Add a new feature capsule and run Router + agents + Sentinel gates.”
* Non-functional and integration requirements that constrain future implementation work but do not specify particular libraries, frameworks, or code-level APIs.

Keep this spec focused on behavior and capabilities, not on the internal Python module layout or specific implementation details.
