# Scribe - Playbook

## Checklist
- Capsule and Allowed Context reviewed.
- Provenance headers updated.
- IMPLEMENTATION / ARCHITECTURE / CONTRIBUTING / CHANGELOG touched if scope requires.
- Doc comments added for every exported surface.
- Verification commands listed (or "n/a" if no tooling exists).

## Flow
1. INVENTORY
   - List every file mentioned in Required Outputs; open only those paths.

2. HEADERS FIRST
   - Insert or update a provenance header at the top of each file:
     - Produced-By=SCRIBE
     - RulesHash=SCRIBE@1.2
     - Decision-ID=<id>

3. DOC COMMENTS
   - Add JSDoc/TSdoc (or language equivalent) covering intent, params, returns, Decision-ID.

4. IMPLEMENTATION NOTES
   - Update IMPLEMENTATION.md at the path specified by the capsule (root or .sentinel/context/).
   - Include file map, call chain, and run instructions impacted by this capsule.

5. CHANGELOG
   - When behavior changed, append an entry to CHANGELOG.md referencing the Decision-ID.

6. VERIFICATION
   - Run doc linters or at minimum spell-check / markdown lint if available.
   - Preferred command name: pnpm lint:docs (or the project’s equivalent).

## Escalate When
- Capsule references files outside Allowed Context.
- Decision-ID is missing or unclear.
- Documentation would expose secrets or redactable info; pause and request guidance.
