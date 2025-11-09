## Scope
SentinelKit extends GitHub's Spec-Kit with contract enforcement, sentinel regression harnesses, provenance logs, and prompt orchestration so AI agents can operate deterministically. The current focus is wiring these primitives into the upstream flow (CLI tooling, docs, and agent prompts) before layering higher-order planning features and capsule automation.

## Current State
- Task 5 remains the capsule baseline: `.sentinel/templates/capsule.md`, `.sentinel/scripts/capsule-create.mjs`, and `.sentinel/scripts/lib/allowed-context.mjs` (plus tests under `.sentinel/tests/capsule-create.test.ts` + `.sentinel/tests/sentinels/sentinel_capsule_context.test.ts`) keep capsules deterministic and <=300 lines.
- Task 6.x is wrapped: agent discovery + Eta templates (`.sentinel/scripts/orch/agents.mjs`, `.sentinel/prompts/router.prompt.eta.md`, `.sentinel/prompts/agent.prompt.eta.md`) feed the refactored renderer (`.sentinel/scripts/orch/prompt-render.mjs`) with schema validation, JSONL logging, smoke runner (`.sentinel/scripts/orch/prompt-render.smoke.mjs`), and docs/snippets already synced via md-surgeon.
- Task 7 delivered context budgets: `.sentinel/context/context-limits.json` + schema, loader (`.sentinel/scripts/context/config.mts`), the `pnpm --dir=.sentinel context:lint` CLI, and renderer integration that aborts when capsules exceed include-list limits. Docs now mention running the linter and pre-commit hook.
- Task 8 shipped MCP contract-validate server + smoke harness; Task 9 added the shared MCP bootstrap, sentinel-run server (`vitest run --config vitest.config.sentinel.ts --reporter=json` via Node) + decision-log server, each with smoke scripts and `pnpm mcp:*` commands documented in README + `.specify/README.md`.
- Tooling/tests snapshot: `pnpm --dir=.sentinel lint`, `pnpm --dir=.sentinel typecheck`, `pnpm --dir=.sentinel vitest run tests/orch/agents.test.ts tests/orch/prompt-render.test.ts tests/mcp/*.test.ts`, `pnpm --dir=.sentinel context:lint`, `pnpm --dir=.sentinel validate:contracts`, `pnpm --dir=.sentinel test:sentinels -- --reporter=json`, plus MCP smokes (`pnpm --dir=.sentinel mcp:sentinel-run:smoke`, `mcp:decision-log:smoke`, `mcp:contract-validate:smoke`).

## Next Subtasks
1. **Verify Tasks 8–10 end-to-end**
   - Re-run `pnpm --dir=.sentinel validate:contracts`, `pnpm --dir=.sentinel vitest run tests/mcp/*.test.ts`, `pnpm --dir=.sentinel mcp:*:smoke`, `pnpm --dir=.sentinel context:lint`, and `pnpm --dir=.sentinel test:sentinels -- --reporter=json` to confirm MCP servers, linter, and sentinel suites remain green on fresh installs (CI parity).
2. **Draft PRD – Spec-Kit CLI Sentinel integration (turnkey onboarding)**
   - Outline `specify init --sentinel` flow (CLI flag semantics, prompts, defaults).
   - Define artifacts copied into new repos: router/agent prompts, `.sentinel/**` workspace, MCP scripts, agents roster, workflow YAML, PR template.
   - Describe post-init steps (running capsule generator, configuring MCP servers, decision-log initialization).
   - Success criteria: zero manual steps beyond `specify init --sentinel`, Spec-Kit iterative workflow untouched, CI badge + MCP instructions present.

## Known Landmines
- Docs via md-surgeon: managed sections (README/UPSTREAM) must be edited through .sentinel/scripts/md-surgeon.mjs + .sentinel/snippets/*.md; manual edits risk desync.
- Windows quoting: inline multiline commands easily break—prefer snippet + md-surgeon flow instead of raw heredocs.
- Ledger locking: .sentinel/DECISIONS.md is append-only via the CLI; manual edits can corrupt NEXT_ID or leave .lock files behind.
- MCP servers run via pnpm scripts; on Windows we spawn Vitest through Node (`process.execPath` + CLI). If you see `spawn EINVAL`, double-check you’re not invoking `.cmd` directly.
- Decision-log smoke tests set `SENTINEL_DECISION_LOG_DRY_RUN=1` to avoid real ledger writes. Clear that env var before running the actual CLI.
- CI jobs reinstall dependencies per job—if you add new packages, ensure both root and `.sentinel/` lockfiles stay in sync or the workflow will fail during `pnpm install --frozen-lockfile`.

## Pointers
- Decision log CLI/tests: .sentinel/scripts/decision-log.mjs, .sentinel/tests/decision-log.test.ts.
- Contract validator + CLI: .sentinel/scripts/contracts/validator.mjs, .sentinel/scripts/contract-validate.mjs.
- Sentinel harness + helper: .sentinel/tests/sentinels/**, .sentinel/tests/sentinels/helpers/fixture-loader.mjs.
- Prompt renderer + templates: .sentinel/scripts/orch/prompt-render.mjs, .sentinel/prompts/{sentinel.router.md,sentinel.capsule.md,router.prompt.eta.md,agent.prompt.eta.md}, and `.sentinel/scripts/orch/agents.mjs`.
- MCP servers + smokes: `.sentinel/scripts/mcp/lib/bootstrap.mjs`, `mcp/sentinel-run.mjs`, `mcp/decision-log.mjs`, `mcp/contract-validate-server.mjs`, tests under `.sentinel/tests/mcp/**`, and smoke scripts `.sentinel/scripts/mcp/*-smoke.mjs`.
- Lint/CI context plan + badge: `.sentinel/context/IMPLEMENTATION.md`, `.github/workflows/sentinel-kit.yml`, README `.mcp` snippet, `.specify/README.md`.
- PR template + enforcement checklist: `.github/pull_request_template.md`.
- md-surgeon + snippets: .sentinel/scripts/md-surgeon.mjs, .sentinel/snippets/*.md.
