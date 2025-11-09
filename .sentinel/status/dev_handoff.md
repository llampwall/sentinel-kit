## Scope
SentinelKit extends GitHub's Spec-Kit with contract enforcement, sentinel regression harnesses, provenance logs, and prompt orchestration so AI agents can operate deterministically. The current focus is wiring these primitives into the upstream flow (CLI tooling, docs, and agent prompts) before layering higher-order planning features and capsule automation.

## Current State
- Task 5 is complete: `.sentinel/templates/capsule.md` defines the reusable capsule skeleton, `.sentinel/scripts/capsule-create.mjs` hydrates it from Spec/Plan/Tasks, and `.sentinel/scripts/lib/allowed-context.mjs` validates include lists (see `.sentinel/tests/capsule-create.test.ts` + `.sentinel/tests/sentinels/sentinel_capsule_context.test.ts` for coverage).
- Task 6.1–6.3 are complete: agent discovery + Eta templates (`.sentinel/scripts/orch/agents.mjs`, `.sentinel/prompts/router.prompt.eta.md`, `.sentinel/prompts/agent.prompt.eta.md`), the refactored renderer (`.sentinel/scripts/orch/prompt-render.mjs`) with CLI options, schema validation + JSONL logging, and the Vitest suite (`.sentinel/tests/orch/{agents,prompt-render}.test.ts`) now covers helper APIs, CLI flows, and log writes.
- New smoke runner: `.sentinel/scripts/orch/prompt-render.smoke.mjs` previews router + capsule prompts for `.specify/specs/005-capsule-gen/capsule.md` (override capsule/agent args as needed).
- Tooling/tests: run from repo root with `pnpm --dir=.sentinel lint`, `pnpm --dir=.sentinel typecheck`, `pnpm --dir=.sentinel vitest run tests/capsule-create.test.ts`, `pnpm --dir=.sentinel vitest run tests/orch/agents.test.ts tests/orch/prompt-render.test.ts`, and `pnpm --dir=.sentinel test:sentinels -- --testNamePattern capsule-context`.

## Next Subtasks
1. **Task 6.5 – Documentation updates**
   - Refresh README/.specify docs with the new CLI usage, logging paths, smoke script, and testing guidance now that renderer work (6.1–6.4) is wrapped.

## Known Landmines
- Docs via md-surgeon: managed sections (README/UPSTREAM) must be edited through .sentinel/scripts/md-surgeon.mjs + .sentinel/snippets/*.md; manual edits risk desync.
- Windows quoting: inline multiline commands easily break—prefer snippet + md-surgeon flow instead of raw heredocs.
- Ledger locking: .sentinel/DECISIONS.md is append-only via the CLI; manual edits can corrupt NEXT_ID or leave .lock files behind.

## Pointers
- Decision log CLI/tests: .sentinel/scripts/decision-log.mjs, .sentinel/tests/decision-log.test.ts.
- Contract validator + CLI: .sentinel/scripts/contracts/validator.mjs, .sentinel/scripts/contract-validate.mjs.
- Sentinel harness + helper: .sentinel/tests/sentinels/**, .sentinel/tests/sentinels/helpers/fixture-loader.mjs.
- Prompt renderer + templates: .sentinel/scripts/orch/prompt-render.mjs, .sentinel/prompts/{sentinel.router.md,sentinel.capsule.md,router.prompt.eta.md,agent.prompt.eta.md}, and `.sentinel/scripts/orch/agents.mjs`.
- md-surgeon + snippets: .sentinel/scripts/md-surgeon.mjs, .sentinel/snippets/*.md.
