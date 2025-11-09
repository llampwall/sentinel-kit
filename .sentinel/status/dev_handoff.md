## Scope
SentinelKit extends GitHub's Spec-Kit with contract enforcement, sentinel regression harnesses, provenance logs, and prompt orchestration so AI agents can operate deterministically. The current focus is wiring these primitives into the upstream flow (CLI tooling, docs, and agent prompts) before layering higher-order planning features and capsule automation.

## Current State
- Code changes: .sentinel/scripts/decision-log.mjs, .sentinel/tests/decision-log.test.ts, .sentinel/scripts/md-surgeon.mjs, .sentinel/snippets/{decision-log.md,upstream-decision.md}, .sentinel/DECISIONS.md, README.md, UPSTREAM.md, sentinel test suite, contract validator, prompt renderer.
- Tooling/tests: "cd .sentinel && pnpm test" passes (contract validator, sentinel harness, decision-log CLI). "pnpm lint" and "pnpm typecheck" also pass with the updated md-surgeon flow.
- Remaining work: Task 5 (capsule template + generator + Allowed Context linting) is untouched; Task 6+ follow per PRD.

## Next Subtasks
1. Task 5.1 - Capsule template skeleton
   - Add .specify/specs/<id>/capsule.md template with Goal/Outputs/Acceptance/Allowed Context/Router Notes.
   - Acceptance: template committed, docs reference it, md-surgeon snippet renders in README/PRD without lint errors.
2. Task 5.2 - Capsule generator CLI
   - Implement .sentinel/scripts/capsule-create.mjs (tsx/Node) + "pnpm capsule:create --spec <path>" that hydrates the template, enforces <300 lines, and hashes capsule IDs.
   - Acceptance: Vitest CLI test shows deterministic capsule output; README documents usage.
3. Task 5.3 - Allowed Context autopop + validation
   - Build helper that scans .sentinel/context/** and emits validated include lists; generator consumes it.
   - Acceptance: unit tests cover valid/missing paths; generator refuses invalid include lists; CI step runs the linter.

## Known Landmines
- Docs via md-surgeon: managed sections (README/UPSTREAM) must be edited through .sentinel/scripts/md-surgeon.mjs + .sentinel/snippets/*.md; manual edits risk desync.
- Windows quoting: inline multiline commands easily break—prefer snippet + md-surgeon flow instead of raw heredocs.
- Ledger locking: .sentinel/DECISIONS.md is append-only via the CLI; manual edits can corrupt NEXT_ID or leave .lock files behind.

## Pointers
- Decision log CLI/tests: .sentinel/scripts/decision-log.mjs, .sentinel/tests/decision-log.test.ts.
- Contract validator + CLI: .sentinel/scripts/contracts/validator.mjs, .sentinel/scripts/contract-validate.mjs.
- Sentinel harness + helper: .sentinel/tests/sentinels/**, .sentinel/tests/sentinels/helpers/fixture-loader.mjs.
- Prompt renderer + templates: .sentinel/scripts/orch/prompt-render.mjs, .sentinel/templates/prompts/*.eta.mts.
- md-surgeon + snippets: .sentinel/scripts/md-surgeon.mjs, .sentinel/snippets/*.md.
