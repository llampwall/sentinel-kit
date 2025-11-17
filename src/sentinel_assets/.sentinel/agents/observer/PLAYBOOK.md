# Observer - PLAYBOOK

1) ASSESS
   - Read capsule Goal and Acceptance.
   - Sample current logs; list gaps (no JSON, missing request_id, noisy stacktraces).

2) PROPOSE
   - Draft /ops/logging/schema.json with required fields.
   - Write /ops/logging/conventions.md (levels, examples, field glossary).
   - Author /ops/errors/policy.md (error classes -> log level, retry/backoff).
   - Create /ops/logging/redaction.json (keys, patterns, justification).
   - Outline /ops/telemetry/plan.md (metrics/traces/events, cardinality, retention).

3) PLAN
   - If code changes are needed, produce /ops/observer/patch-plan.md:
     - Files to touch, minimal diffs, acceptance checks.
     - Explicitly state: no feature logic changes.

4) VERIFY
   - Specify sentinel checks under /.sentinel/tests/sentinels/** that assert:
     - Logs are JSON with required fields.
     - Correlation IDs propagate across one representative request/job.
     - Redaction rules apply (e.g., secret-like values are masked).
   - Coordinate with Verifier to run suites locally and in CI.

5) PACKAGE
   - Finalize artifacts and runbook:
     - /ops/logging/runbook.md with jq/grep examples, common queries, incident triage steps.
   - Include Decision-ID and capsule in headers.

6) HANDOFF
   - Assign Builder to implement patch-plan (instrumentation shims/middleware).
   - Assign Releaser to add CI log-format assertions and sentinel runs.
   - If external telemetry is required, assign Integrator to configure client and secrets.

Notes:
- Prefer lightweight, structured logging libraries (e.g., pino/winston); tracing via OpenTelemetry if/when enabled.
- Keep cardinality low and redact aggressively; logs are for operators, not analytics.
