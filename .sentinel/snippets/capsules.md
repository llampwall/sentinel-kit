<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0010 -->
### Capsule workflow

Capsules turn a Spec-Kit feature (`.specify/specs/<slug>`) into a router-ready hand-off with explicit Allowed Context.

1. Start from the reusable template at `.sentinel/templates/capsule.md` (the generator copies this structure automatically if you prefer CLI-driven capsules).
2. Update the Spec-Kit feature (spec.md, plan.md, tasks.md). Capsule Task 5 lives in `.specify/specs/005-capsule-gen`.
2. Render the capsule from the `.sentinel/` workspace:
   ```bash
   pnpm -C .sentinel capsule:create --spec ../.specify/specs/005-capsule-gen --decision D-XXXX
   ```
   - `--decision` must be the next ledger ID from `.sentinel/DECISIONS.md`.
   - Pass `--agent`/`--rulesHash` if the capsule belongs to someone other than ROUTER.
3. Review the generated `.specify/specs/<slug>/capsule.md` and keep it under 300 lines. The CLI hashes the ID (e.g., `005-capsule-gen@<hash>`) and auto-includes `.sentinel/context/**` via the Allowed Context helper.
4. Run the deterministic tests any time capsule logic changes:
   ```bash
   pnpm -C .sentinel vitest run tests/capsule-create.test.ts
   pnpm -C .sentinel test:sentinels -- --testNamePattern capsule-context
   ```
   Both commands execute inside `.sentinel/`.
5. When docs mention capsules, edit `.sentinel/snippets/capsules.md` and re-run `node .sentinel/scripts/md-surgeon.mjs` so README stays in sync.

