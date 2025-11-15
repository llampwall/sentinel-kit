# Integrator - PLAYBOOK

1) SPECIFY
   - Record provider base URL(s), auth type (key, OAuth, webhook secret), expected throughput, and error model.
   - List resources/endpoints with required params and rate-limit notes.

2) CONTRACT
   - Create/refresh:
     - .sentinel/contracts/<provider>.<resource>.vN.yaml
     - .sentinel/contracts/fixtures/<provider>.<resource>.vN/good/*.json
     - .sentinel/contracts/fixtures/<provider>.<resource>.vN/bad/*.json
   - Run: pnpm -C .sentinel validate:contracts (expect failing first if drift exists).

3) IMPLEMENT
   - Add client at /src/clients/<provider>/<resource>.ts:
     - auth, retries/backoff (with jitter), circuit breaker, rate limiting
     - request/response validation against schema
     - structured logs per Observer schema (no secrets)
   - Expose a minimal, typed surface (pure functions returning DTOs).

4) VERIFY
   - Unit/integration tests under /tests/clients/<provider>/*.test.ts
   - Contract check: pnpm -C .sentinel validate:contracts
   - Sentinel smoke: .sentinel/tests/sentinels/integrations/<provider>/*.mjs
   - Prove a failing case (bad fixture) then passing with current code.

5) PACKAGE
   - Write /ops/integrations/<provider>/README.md:
     - env vars and secret names, scopes, rate-limit math, quotas, expected SLAs
     - troubleshooting matrix (common upstream errors -> client behavior)
   - Include provenance headers across artifacts.

6) HANDOFF
   - Releaser: wire CI gates for contracts + integration tests + sentinels.
   - Observer: confirm log fields and redaction rules.
   - Scribe: polish docs and link from main README.

Notes:
- Prefer small, composable clients per resource; avoid “god” clients.
- Version contracts on any upstream change; never silently widen types.
- If a provider is unstable, add a canary sentinel that pings a single cheap endpoint daily.
