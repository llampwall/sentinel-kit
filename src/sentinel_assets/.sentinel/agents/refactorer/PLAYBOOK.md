# Refactorer - PLAYBOOK

1) ASSESS
   - Read capsule Goal and Acceptance; list invariants (no behavior change, no API change).
   - Capture baseline metrics to /refactors/<capsule>/metrics-before.json.

2) PLAN
   - Author /refactors/<capsule>/plan.md:
     - Goals, non-goals, invariants
     - Acceptance checks (all tests/contracts/sentinels must pass)
     - Rollback steps (git commands, files to revert)
   - Draft /refactors/<capsule>/map.json (symbols/files to move/rename).

3) STAGE
   - Write codemods under /refactors/<capsule>/codemods/*.ts (if applicable).
   - Dry-run codemods; attach example diffs in plan.md.
   - Identify any docs or tests gaps; pre-create Router notes to queue Scribe/Verifier.

4) TRANSFORM
   - Apply changes in small, reviewable commits (mechanical first, hand-edits last).
   - Maintain deprecation shims where needed; update import barrels.

5) VERIFY
   - Run gates locally:
     - pnpm test
     - pnpm -C .sentinel test
     - pnpm -C .sentinel validate:contracts
   - Recompute metrics to /refactors/<capsule>/metrics-after.json and compare.
   - If any behavior change is detected, STOP and escalate to Router.

6) PACKAGE
   - Update /refactors/<capsule>/risk.md with final blast radius and mitigations.
   - Summarize diffs and confirm acceptance checks passed in plan.md.
   - Ensure provenance headers are present in artifacts.

7) HANDOFF
   - Queue Verifier to add/adjust tests if gaps were found.
   - Queue Scribe to update docs/ADR if module boundaries or names changed.
   - Notify Releaser if CI cache keys or build times are impacted.

Notes:
- Keep transforms deterministic and idempotent.
- Prefer automated edits over manual search/replace.
- Limit PR scope; if the plan grows, split into sequenced capsules.
