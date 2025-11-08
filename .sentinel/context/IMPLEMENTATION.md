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
