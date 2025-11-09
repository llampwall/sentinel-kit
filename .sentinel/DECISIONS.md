<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0004 -->

# Decisions Ledger

## NEXT_ID
D-0007

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
