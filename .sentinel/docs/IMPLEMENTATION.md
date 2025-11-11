# Implementation

## Current Enforcement Surface
- `.sentinel/contracts/users.v1.yaml` + `fixtures/users.v1/get_active.json` – sample contract + payload pair that exercises the validation tooling.
- `.sentinel/scripts/contracts/validate.mjs` – CLI validator invoked via `pnpm --dir=.sentinel validate:contracts`, walks every contract/fixture pairing, and exits non-zero on schema failures.
- `.sentinel/scripts/mcp/contract-validate-server.mjs` – JSON-RPC/stdio server that exposes the same validation logic to MCP clients via the shared MCP bootstrap; exercised by Vitest integration tests and `pnpm --dir=.sentinel mcp:contract-validate:smoke`.
- `.sentinel/scripts/mcp/sentinel-run.mjs` + `.sentinel/scripts/mcp/decision-log.mjs` – expose `sentinel_run` and `decision_log` tools backed by Vitest and the ledger CLI, with smoke scripts wired into CI.
- `.sentinel/tests/sentinels/sentinel_users_email_format.test.mjs` plus `tests/sentinels/sentinel_capsule_context.test.ts` – regression harnesses that guard contract behavior and Allowed Context limits.
- `.sentinel/scripts/orch/prompt-render.mjs` + `.sentinel/prompts/*` – router/agent prompt renderer that auto-discovers agents under `.sentinel/agents/**`, injects capsule content, and validates router JSON.
- `.sentinel/DECISIONS.md` – decision ledger template that enforces provenance headers + NEXT_ID tracking.

## Execution Flow
1. **Contracts**: `validate.mjs` loads each `<domain>.vN` schema, compiles it with AJV, and validates every JSON fixture under `fixtures/<contract>/**`. The MCP server reuses the same helpers so external agents can trigger validations.
2. **Sentinels**: The sentinel suite imports the shared fixture loader, mutates data to simulate regressions, and asserts the contract validator rejects invalid payloads. Future sentinels follow the same pattern.
3. **Router Prompts**:
   - `prompt-render.mjs --mode router` reads `.sentinel/prompts/sentinel.router.md`, injects capsule text, and lists available agents discovered from `.sentinel/agents/*/ROLE.md`.
   - After the router responds with JSON, rerun in `--mode capsule --agent <id>` to emit the agent prompt (`.sentinel/prompts/sentinel.capsule.md`) scoped to the selected agent + capsule Allowed Context.
4. **Artifacts**: Every change is expected to add a provenance header plus a new entry in `DECISIONS.md`, keeping artifact memory decoupled from chat history.

## Known Gaps
- Prompt renderer still requires two invocations (router → capsule) and manual JSON capture; future work can streamline that flow but it is tracked outside Tasks 8‑10.
- Capsule docs readouts depend on the shared snippets and md-surgeon; keep using the snippet workflow whenever CI/mcp instructions evolve to avoid README drift.

## CI Workflow (Task 10)
`.github/workflows/sentinel-kit.yml` now runs on pushes/PRs targeting `main` plus `workflow_dispatch`, with `concurrency.group = sentinel-kit-${{ github.ref }}` to cancel redundant builds. Jobs:

1. **setup-toolchain** (ubuntu + windows): checkout, `actions/setup-node@v4` pinned to 20.17 with pnpm cache, `corepack enable`, `pnpm install` at root and `.sentinel/`, and uv cache restore. Step summary records the pnpm store path per runner.
2. **contracts** (matrix) runs `pnpm --dir=.sentinel validate:contracts` after reusing the toolchain steps; failed runs upload validator logs.
3. **sentinels** (matrix) executes `pnpm --dir=.sentinel vitest run --config vitest.config.sentinel.ts --reporter=json`, teeing output to `sentinel-report.json` and always uploading the artifact.
4. **mcp-smoke** (ubuntu) sequentially runs the three smoke scripts to prove contract-validate, sentinel-run, and decision-log servers handshake correctly.
5. **docs-lint** (ubuntu) runs `pnpm --dir=.sentinel context:lint`.

README plus `.specify/README.md` render the workflow badge via `md-surgeon`, and the PR template lists capsule, decision-log, sentinel, context lint, and optional MCP smoke checklist items. Ensure future CI changes go through `.sentinel/snippets/workflow-badge.md` so both docs stay in sync.
