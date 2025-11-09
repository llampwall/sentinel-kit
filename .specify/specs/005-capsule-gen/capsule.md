<!-- ProducedBy=ROUTER RulesHash=ROUTER@1.0 Decision=D-0010 -->

# Capsule 005-capsule-gen@45f68a75

## Goal
SentinelKit capsules must capture Task 5 (template, generator CLI, Allowed Context enforcement) so routers can mount exactly the files required for provenance-safe automation. The capsule should summarize the work, the deliverables, and the acceptance bullets that currently live in the developer handoff doc.

## Required Outputs
- Capsule template at `.specify/specs/005-capsule-gen/capsule.md` seeded with Goal, Required Outputs, Acceptance Criteria, Allowed Context, and Router Notes sections plus a ProducedBy header.
- CLI entry `pnpm -C .sentinel capsule:create --spec <dir>` backed by `.sentinel/scripts/capsule-create.mjs` with tests that snapshot deterministic output.
- Allowed Context helper under `.sentinel/scripts/lib/allowed-context.mjs` plus sentinel coverage to enforce valid include lists.
- README section (managed via md-surgeon snippet) that documents how to render capsules and run the new tests.

## Acceptance Criteria
- Template committed, snippet/docs updated if referenced, and `pnpm -C .sentinel lint` remains clean.
- Generator hydrates spec/plan/tasks into <=300-line capsules, enforces hashed IDs, refuses invalid include lists, and `pnpm -C .sentinel vitest run tests/capsule-create.test.ts` passes.
- Allowed Context helper auto-mounts `.sentinel/context/**`, dedupes + validates includes, feeds the generator, and `pnpm -C .sentinel test:sentinels -- --filter capsule-context` stays green.

## Allowed Context
- .sentinel/context/IMPLEMENTATION.md
- .sentinel/context/SentinelKit_salvage_plan.md
- .sentinel/context/SentinelKit_thesis.md
- .sentinel/context/todo - specify-cli integration.txt
- .sentinel/scripts/capsule-create.mjs
- .sentinel/scripts/lib/allowed-context.mjs
- .sentinel/scripts/md-surgeon.mjs
- .sentinel/snippets/capsules.md
- .sentinel/status/dev_handoff.md
- .sentinel/tests/capsule-create.test.ts
- .sentinel/tests/sentinels/sentinel_capsule_context.test.ts
- .specify/specs/005-capsule-gen/plan.md
- .specify/specs/005-capsule-gen/spec.md
- .specify/specs/005-capsule-gen/tasks.md
- .taskmaster/tasks/tasks.json
- README.md

## Router Notes
- Builder executes the CLI + helper changes; Scribe only enters once docs expand past snippets.
- Keep capsules under 300 lines; split into multiple specs if this one bloats past the budget.
- Mount `.sentinel/context/**` plus the include list above when prompting router/agents; anything missing must be added to the spec, not improvised mid-flight.
