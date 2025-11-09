# Implementation

## Current Enforcement Surface
- `.sentinel/contracts/users.v1.yaml` + `fixtures/users.v1/get_active.json` — sample contract + payload pair that exercises the validation tooling.
- `.sentinel/scripts/contracts/validate.mjs` — CLI validator invoked via `npm run validate:contracts`, walks every contract/fixture pairing, and exits non-zero on schema failures.
- `.sentinel/scripts/mcp/contract-validate-server.mjs` — JSON-RPC/stdio server that exposes the same validation logic to MCP clients (handshake currently broken; smoke tests still TODO).
- `.sentinel/tests/sentinels/sentinel_users_email_format.test.mjs` — Vitest-based sentinel demonstrating how regressions are encoded as focused suites.
- `.sentinel/scripts/orch/prompt-render.mjs` + `.sentinel/prompts/*` — router/agent prompt renderer that auto-discovers agents under `.sentinel/agents/**` and injects capsule content.
- `.sentinel/DECISIONS.md` — decision ledger template that enforces provenance headers + NEXT_ID tracking.

## Execution Flow
1. **Contracts**: `validate.mjs` loads each `<domain>.vN` schema, compiles it with AJV, and validates every JSON fixture under `fixtures/<contract>/**`. The MCP server reuses the same helpers so external agents can trigger validations.
2. **Sentinels**: The sentinel suite imports the shared fixture loader, mutates data to simulate regressions, and asserts the contract validator rejects invalid payloads. Future sentinels follow the same pattern.
3. **Router Prompts**:
   - `prompt-render.mjs --mode router` reads `.sentinel/prompts/sentinel.router.md`, injects capsule text, and lists available agents discovered from `.sentinel/agents/*/ROLE.md`.
   - After the router responds with JSON, rerun in `--mode capsule --agent <id>` to emit the agent prompt (`.sentinel/prompts/sentinel.capsule.md`) scoped to the selected agent + capsule Allowed Context.
4. **Artifacts**: Every change is expected to add a provenance header plus a new entry in `DECISIONS.md`, keeping artifact memory decoupled from chat history.

## Known Gaps
- `contract-validate-smoke.mjs` proves the MCP server path end-to-end, but we still need equivalent coverage for upcoming `sentinel-run` and `decision-log` servers once they land.
- The router flow currently requires two manual invocations; future tasks should collapse it into a single run that captures the router JSON automatically.

## CI Workflow Plan (Task 10.1)
Goal: design `.github/workflows/sentinel-kit.yml` that enforces contracts, sentinels, MCP smoke tests, and docs linting across Ubuntu + Windows. Implementation follows in Tasks 10.2+.

### Triggers & Metadata
- `on`:
  - `push`: `main` (protects trunk)
  - `pull_request`: branches targeting `main`
  - `workflow_dispatch`: optional manual runs
- `concurrency`: `group: sentinel-kit-${{ github.ref }}` + `cancel-in-progress: true` to avoid duplicate matrix runs.
- Required permissions: `contents: read`, `checks: write` (for status reporting), `pull-requests: write` (future auto-comments).

### Shared Inputs / Environment
- Node `20.17.x` via `actions/setup-node` (pnpm cache enabled).
- `PNPM_VERSION` pinned to workspace value; `pnpm fetch` + `pnpm install --frozen-lockfile` within `.sentinel/`.
- `UV_CACHE_DIR`: `${{ runner.temp }}/uv-cache`.
- `VITEST_JSON=1` so sentinel job emits deterministic JSON if needed downstream.
- Reusable `setup-toolchain` job output: `pnpm_store_path`, `workspace_hash` (hashFiles of lockfiles) for cache keys.

### Job Overview
1. **setup-toolchain (matrix: ubuntu-latest, windows-latest)**
   - Steps:
     1. `actions/checkout`
     2. Restore pnpm cache (`actions/setup-node` w/ `cache: pnpm`).
     3. `corepack enable` then `pnpm install` at repo root, `pnpm --dir=.sentinel install --frozen-lockfile`.
     4. Cache uv: `actions/cache` w/ key `${{ runner.os }}-uv-${{ hashFiles('.tool-versions','uv.lock') }}`.
   - Outputs: `pnpm_store_path`, `sentinel_dir`.

2. **contracts (needs: setup)**
   - Runs on same OS matrix.
   - Steps: reuse caches, run `pnpm --dir=.sentinel validate:contracts`.
   - On failure: upload `.sentinel/contracts/*.log` (if produced).

3. **sentinels (needs: setup)**
   - Uses matrix.
   - Command: `vitest run --config vitest.config.sentinel.ts --reporter=json`.
   - Parse JSON to fail if `success=false`; keep artifact of `sentinel-report.json`.

4. **mcp-smoke (needs: setup)**
   - Matrix optional (we can limit to ubuntu for speed; Windows coverage already via sentinel job).
   - Commands (sequential):
     - `pnpm --dir=.sentinel mcp:contract-validate:smoke`
     - `pnpm --dir=.sentinel mcp:sentinel-run:smoke`
     - `pnpm --dir=.sentinel mcp:decision-log:smoke`
   - Each emits `[tool] smoke test passed.`; failure surfaces tool errors.

5. **docs-lint (needs: setup)**
   - Runs `pnpm --dir=.sentinel context:lint`.
   - Future: add Markdown lint or `pnpm lint` subset if needed.

6. **docs-badge (optional)**
   - After other jobs succeed, update README badge (manual step for now). Implementation detail deferred.

### Artifacts / Notifications
- On failure, upload `vitest-report.json` and logs (`mcp-smoke.log`) for easier triage.
- Consider Slack/GitHub notification once workflow stabilized (not required in plan).

### Required Follow-ups
- README + `.sentinel/context/IMPLEMENTATION.md` need a badge + short paragraph once workflow exists (Task 10.4).
- PR template needs checkboxes for capsule + decision log + sentinel updates (Task 10.5).
- Workflow file will live at `.github/workflows/sentinel-kit.yml`; future tasks implement YAML + caching specifics.
