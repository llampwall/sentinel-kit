# Builder - Playbook

## Checklist
- Capsule and Allowed Context reviewed.
- Edit plan drafted before coding.
- Provenance headers added or updated (ASCII-only).
- Contracts/tests/sentinels run or justified.
- Verification commands listed exactly.

## Flow
1) PLAN
   - Write a numbered list of edits (file -> intent).
   - If uncertain about scope, ask for capsule update before code changes.

2) IMPLEMENT
   - Apply edits file-by-file with minimal diffs.
   - Insert provenance header at top of every modified file:
     - Produced-By=BUILDER
     - RulesHash=BUILDER@1.2
     - Decision-ID=<id>

3) VERIFY
   - Contracts: `pnpm -C .sentinel validate:contracts`
   - Tests: `pnpm test`
   - Sentinels (if the capsule requires them): run under `.sentinel/tests/sentinels/**`
   - Capture a short results summary (pass/fail counts or key outputs).

4) PACKAGE
   - Return: numbered edit plan, unified diffs, verification commands and summary.
   - Note any follow-ups (e.g., Verifier for missing tests, Scribe for docs, Releaser for CI wiring).

## Escalate When
- Capsule does not grant access to a required file or directory.
- Acceptance Criteria conflict with existing contracts or sentinels.
- Tests fail in unrelated areas; request a focused capsule or split scope.
