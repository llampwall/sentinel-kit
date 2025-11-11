# Capsule Automation Plan

## Implementation Surfaces
- `.specify/specs/005-capsule-gen/capsule.md` must exist so routers can hand Task 5 to Codex agents.
- `.sentinel/scripts/capsule-create.mjs` exposes `pnpm -C .sentinel capsule:create --spec <dir>` and renders the capsule text.
- `.sentinel/scripts/lib/allowed-context.mjs` owns Allowed Context discovery, deduplication, and validation logic.
- `.sentinel/tests/capsule-create.test.ts` exercises deterministic output; `.sentinel/tests/sentinels/sentinel_capsule_context.test.ts` guards the helper contract.
- `.sentinel/snippets/capsules.md` + README marker document how to create/run capsules.

## Allowed Context Seeds
- .specify/specs/005-capsule-gen/spec.md
- .specify/specs/005-capsule-gen/plan.md
- .specify/specs/005-capsule-gen/tasks.md
- .sentinel/scripts/capsule-create.mjs
- .sentinel/scripts/lib/allowed-context.mjs
- .sentinel/tests/capsule-create.test.ts
- .sentinel/tests/sentinels/sentinel_capsule_context.test.ts
- .sentinel/snippets/capsules.md
- .sentinel/scripts/md-surgeon.mjs
- README.md
- .sentinel/status/dev_handoff.md
- .taskmaster/tasks/tasks.json

## Router Notes
- Builder executes the CLI + helper changes; Scribe only enters once docs expand past snippets.
- Keep capsules under 300 lines; split into multiple specs if this one bloats past the budget.
- Mount only the include list above when prompting router/agents; maintainer notes now live under `.sentinel/notes-dev/**` and should be referenced outside capsules if needed.
