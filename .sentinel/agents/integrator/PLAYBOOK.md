# Integrator · Playbook

## Checklist
- Contracts + fixtures updated/bumped.
- Client isolates auth/retry logic.
- Unit + sentinel tests cover success + failure.
- Env vars documented (no secrets committed).
- Verification commands listed (contract validator + tests).

## Flow
1. **Scope** – Confirm which external systems/endpoints are in scope and list them in the capsule response.
2. **Contracts first** – Add/update `.sentinel/contracts/<service>.vN.*` plus fixtures; bump version on breaking change.
3. **Client implementation** – Build/extend client modules with retries/backoff/circuit breakers + structured errors.
4. **Testing** – Write unit tests for happy/error paths and sentinel tests capturing prior incidents (invalid schema, rate limiting).
5. **Docs** – Summarize configuration requirements for Scribe/README.

## Escalate When
- Provider behavior requires new infrastructure or background jobs.
- Secrets/keys management decisions are undefined.
- Contract changes would ripple to other capsules (coordinate via Decision + new capsules).
