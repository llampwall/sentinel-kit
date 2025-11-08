# Builder · Playbook

## Checklist
- Capsule & Allowed Context reviewed.
- Edit plan drafted before coding.
- Provenance headers added/updated.
- Tests/contracts run or justified.
- Verification commands listed.

## Flow
1. **Plan** – Write a numbered list of edits (files + intent). Get approval via prompt if uncertain.
2. **Implement** – Apply changes file-by-file, keeping diffs minimal. Reference Decision ID in headers.
3. **Verify** – Run `npm run validate:contracts`, `npm test`, or capsule-specific commands. Capture output summary.
4. **Package** – Output diffs and verification plan exactly as prompt requires.

## Escalate When
- Capsule doesn’t grant access to a required file.
- Acceptance Criteria conflict with existing contracts/sentinels.
- Tests fail due to unrelated areas—flag and request new capsule.
