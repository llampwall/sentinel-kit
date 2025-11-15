# Backender - PLAYBOOK

1) ORIENT
   - Read capsule Goal and Acceptance.
   - Note dependencies on Designer (UI) or Integrator (external services).

2) PLAN
   - Enumerate:
     - Endpoints or CLI commands
     - Services and data flow
     - DB schema/migration needs
     - Jobs (queue/cron) and triggers
     - Required config/env vars
   - Write a short checklist of acceptance assertions tied to endpoints/services.

3) DESIGN
   - Define DTOs and validation schemas (e.g., /server/src/schemas/**).
   - Draft a migration plan (forward-only) and fallback/rollback notes.
   - Decide on repository/service interfaces; list log/telemetry fields expected by Observer.

4) IMPLEMENT
   - Add routes/controllers and wire to services.
   - Implement services with pure-core helpers where possible.
   - Create migrations and repositories; seed minimal local test data if helpful.
   - Implement jobs and schedule configuration; keep handlers idempotent.
   - Use Integrator clients for any external calls (do not roll your own HTTP calls here).

5) VERIFY
   - Run `pnpm lint`, `pnpm typecheck`, and build.
   - Execute the repo test suite and any sentinel/contract checks applicable.
   - Local manual checks: 2–3 representative requests through the full stack.
   - Confirm logs adhere to Observer schema (fields present, no secrets).

6) PACKAGE
   - Update /ops/backend/runbook.md:
     - Startup commands, env var matrix, migrations apply/rollback, common queries.
   - Note any DB or infra risks and the exact commands to run in dev/CI.
   - Ensure provenance headers are present in notes/PR.

7) HANDOFF
   - Tag Verifier to extend tests around new routes/services/jobs.
   - Tag Releaser to wire CI steps (migrate, build, test).
   - Tag Observer if new log fields or error classes were introduced.
   - Tag Integrator for any missing external client functions.

Notes:
- Prefer composition and small modules; avoid God services.
- Keep public surface stable; if breaking change is unavoidable, escalate with a dedicated capsule.
