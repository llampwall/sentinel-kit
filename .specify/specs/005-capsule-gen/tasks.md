# Capsule Automation Tasks

## Required Outputs
- Capsule template at `.specify/specs/005-capsule-gen/capsule.md` seeded with Goal, Required Outputs, Acceptance Criteria, Allowed Context, and Router Notes sections plus a ProducedBy header.
- CLI entry `pnpm -C .sentinel capsule:create --spec <dir>` backed by `.sentinel/scripts/capsule-create.mjs` with tests that snapshot deterministic output.
- Allowed Context helper under `.sentinel/scripts/lib/allowed-context.mjs` plus sentinel coverage to enforce valid include lists.
- README section (managed via md-surgeon snippet) that documents how to render capsules and run the new tests.

## Acceptance Criteria
- Template committed, snippet/docs updated if referenced, and `pnpm -C .sentinel lint` remains clean.
- Generator hydrates spec/plan/tasks into <=300-line capsules, enforces hashed IDs, refuses invalid include lists, and `pnpm -C .sentinel vitest run tests/capsule-create.test.ts` passes.
- Allowed Context helper mounts repository-scoped context (if any) under `.sentinel/context/**`, dedupes + validates includes, feeds the generator, and `pnpm -C .sentinel test:sentinels -- --filter capsule-context` stays green. Maintainer notes under `.sentinel/notes-dev/**` are excluded unless explicitly added.
