<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0004 -->

# Decisions Ledger

## NEXT_ID
D-0019

## Format

| Field | Description | Example |
| --- | --- | --- |
| ID | Monotonic `D-####` allocated from `NEXT_ID`. | `D-0005` |
| Date | ISO 8601 date the decision landed. | `2025-11-08` |
| Author | Agent or human authoring the entry. | `Builder` |
| Scope | Files, subsystems, or surfaces impacted. | `.sentinel/scripts/orch/*.mjs` |
| Decision | What changed / was agreed upon. | `Adopt Eta prompt renderer` |
| Rationale | Why the change was necessary. | `Template reuse + logging` |
| Outputs | Concrete artifacts produced (files, PRs). | `prompt-render.mjs, README` |
| Supersedes | Previous decision ID or `none`. | `none` |

Record entries in the order above, separated by blank lines. Keep the ledger under ~300 lines; when it grows larger, move the oldest entries to `DECISIONS.archive.md`.

## ProducedBy Header Spec

Every file touched by a decision must include a provenance header emitted by the decision-log CLI:

```
ProducedBy=<AGENT> RulesHash=<AGENT>@<version> Decision=<D-####> (#<short-hash>)
```

- `<AGENT>`: agent or role identifier (e.g., `BUILDER`).
- `<version>`: the RulesHash version string (`BUILDER@1.2`).
- `<short-hash>`: 7-character git commit hash that introduced the change.
- Use language-appropriate comment wrappers:
  - JS/TS: `/* ProducedBy=... */`
  - Python/Shell: `# ProducedBy=...`
  - Markdown: `<!-- ProducedBy=... -->`

## Log

ID: D-0002
Date: 2025-11-06
Author: Jordan
Scope: .sentinel/contracts/users.v1.yaml
Decision: Clarify users.v1 is an array of user objects (not a single object)
Rationale: Align contract with real fixture shape; unblock validation and unit test
Outputs: .sentinel/contracts/users.v1.yaml, fixtures/users.v1/*
Supersedes: none

ID: D-0003
Date: 2025-11-06
Author: Scribe
Scope: src/users_consumer.mjs; scripts/contracts/validate.mjs; scripts/mcp/*.mjs; tests/**
Decision: Introduce MCP server `contract.validate` and document code
Rationale: Document provenance, explain call flows, and expose validation via MCP tooling
Outputs: scripts/mcp/contract-validate-server.mjs, README docs
Supersedes: none

ID: D-0004
Date: 2025-11-07
Author: Builder
Scope: .sentinel/scripts/orch/prompt-render.mjs; README.md; .sentinel/DECISIONS.md
Decision: Introduce minimal orchestrator CLI + docs to render router/capsule prompts locally
Rationale: Auto-discover agents, mount their context at runtime, and document the workflow for Codex users
Outputs: scripts/orch/prompt-render.mjs, README router section
Supersedes: none

ID: D-0005
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/orch
Decision: Adopt Eta prompt renderer
Rationale: Unified templates + logging
Outputs: .sentinel/scripts/orch/prompt-render.mjs, README.md
Supersedes: none

ID: D-0006
Date: 2025-11-09
Author: Maintainer
Scope: sync/<YYYY-MM-DD>
Decision: Merge spec-kit upstream into sentinel-kit
Rationale: Rebase onto upstream main
Outputs: UPSTREAM.md, .sentinel/**
Supersedes: none

ID: D-0007
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/orch
Decision: Adopt Eta prompt renderer
Rationale: Unified templates + logging
Outputs: .sentinel/scripts/orch/prompt-render.mjs, README.md
Supersedes: none

ID: D-0008
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/orch
Decision: Adopt Eta prompt renderer
Rationale: Unified templates + logging
Outputs: .sentinel/scripts/orch/prompt-render.mjs, README.md
Supersedes: none

ID: D-0009
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/orch
Decision: Adopt Eta prompt renderer
Rationale: Unified templates + logging
Outputs: .sentinel/scripts/orch/prompt-render.mjs, README.md
Supersedes: none

ID: D-0010
Date: 2025-11-09
Author: Builder
Scope: .specify/specs/005-capsule-gen; .sentinel/scripts
Decision: Capsule generator + Allowed Context helper
Rationale: Automate Task 5 capsules, validate include lists, and document the workflow
Outputs: .specify/specs/005-capsule-gen/capsule.md, .sentinel/scripts/capsule-create.mjs, .sentinel/scripts/lib/allowed-context.mjs, .sentinel/tests/capsule-create.test.ts, .sentinel/tests/__snapshots__/capsule-create.test.ts.snap, .sentinel/tests/sentinels/sentinel_capsule_context.test.ts, .sentinel/snippets/capsules.md, README.md, .sentinel/scripts/md-surgeon.mjs
Supersedes: none

ID: D-0011
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/orch/prompt-render.mjs; README.md; .specify/README.md
Decision: Enforce context linter before prompt rendering
Rationale: Prompt rendering should fail fast when capsules exceed include-list rules or line budgets.
Outputs: .sentinel/scripts/orch/prompt-render.mjs, README.md, .specify/README.md
Supersedes: none

ID: D-0012
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/context/**; .sentinel/context; .sentinel/tests/context
Decision: Add context-limits schema + pnpm context:lint
Rationale: Capsule include lists need automated budgets, forbidden-path checks, and reproducible CLI coverage.
Outputs: .sentinel/context/limits/context-limits.json, .sentinel/scripts/context/config.mts, .sentinel/scripts/context/lint.mts, .sentinel/tests/context/config.test.ts, .sentinel/tests/context/lint.test.ts
Supersedes: none

ID: D-0013
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/contracts/*.mjs; .sentinel/scripts/contract-validate.mjs; .sentinel/tests/contracts
Decision: Extract shared contract validator core and update CLI
Rationale: MCP server work needs a reusable validator module and the CLI should consume it while exposing watch hooks.
Outputs: .sentinel/scripts/contracts/validator-core.mjs, .sentinel/scripts/contracts/validator.mjs, .sentinel/scripts/contract-validate.mjs, .sentinel/tests/contracts/validator-core.test.ts
Supersedes: none

ID: D-0014
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/mcp/contract-validate-server.mjs; .sentinel/scripts/mcp/contract-validate-smoke.mjs; .sentinel/tests/mcp/contract-validate-server.test.ts
Decision: Rebuild contract-validate MCP server on vscode-jsonrpc
Rationale: Needed a standards-compliant MCP endpoint that reuses the shared validator core, exposes proper tooling metadata, and ships with automated coverage.
Outputs: .sentinel/scripts/mcp/contract-validate-server.mjs, .sentinel/scripts/mcp/contract-validate-smoke.mjs, .sentinel/tests/mcp/contract-validate-server.test.ts
Supersedes: none

ID: D-0015
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/mcp/lib/bootstrap.mjs; .sentinel/tests/mcp/bootstrap.test.ts
Decision: Add shared MCP bootstrap helper
Rationale: Needed a reusable JSON-RPC server scaffold with Zod validation for upcoming sentinel_run/decision_log MCP endpoints.
Outputs: .sentinel/scripts/mcp/lib/bootstrap.mjs, .sentinel/tests/mcp/bootstrap.test.ts
Supersedes: none

ID: D-0016
Date: 2025-11-09
Author: Builder
Scope: .sentinel/scripts/mcp/sentinel-run.mjs; .sentinel/tests/mcp/sentinel-run.test.ts
Decision: Implement sentinel_run MCP server
Rationale: Expose pnpm test:sentinels via MCP so agents can trigger sentinel suites with optional filters.
Outputs: .sentinel/scripts/mcp/sentinel-run.mjs, .sentinel/tests/mcp/sentinel-run.test.ts
Supersedes: none

ID: D-0018
Date: 2025-11-09
Author: Builder
Scope: .github/workflows/sentinel-kit.yml
Decision: Add sentinel-kit workflow skeleton
Rationale: CI needs a shared setup job with pnpm/uv caching and OS matrix before wiring downstream gates.
Outputs: .github/workflows/sentinel-kit.yml
Supersedes: none
