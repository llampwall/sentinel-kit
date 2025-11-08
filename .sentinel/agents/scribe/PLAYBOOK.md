# Scribe · Playbook

## Checklist
- Capsule + Allowed Context reviewed.
- Provenance headers updated.
- IMPLEMENTATION/ARCHITECTURE/CONTRIBUTING/CHANGELOG touched if scope requires.
- Doc comments added for every exported surface.
- Verification commands listed (or “n/a” if no tooling exists).

## Flow
1. **Inventory files** – List every file mentioned in Required Outputs; open only those paths.
2. **Headers first** – Insert/update provenance comment at the top of each file.
3. **Doc comments** – Add JSDoc/TSdoc (or language equivalent) covering intent, params, returns, Decision ID.
4. **Implementation notes** – Update `.sentinel/context/IMPLEMENTATION.md` with file map, call chain, and run instructions impacted by this capsule.
5. **Change log** – When behavior changed, append entry to `CHANGELOG.md` referencing Decision ID.
6. **Verification** – Run doc linters or at minimum spell-check / markdown lint if available.

## Escalate When
- Capsule references files outside Allowed Context.
- Decision ID is missing or unclear.
- Documentation would expose secrets or redactable info—pause and request guidance.
