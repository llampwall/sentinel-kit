# Capsule Author - PLAYBOOK

1) GATHER
   - Read the relevant thesis/PRD/salvage plan/tasks.
   - Note dependencies (agents, services, files) and constraints (time, scope, tooling).

2) DRAFT
   - Create .specify/specs/<capsule_id>/capsule.md with:
     - Goal, Non-Goals, Scope, Constraints
     - Inputs (links to sources) and Dependencies
     - Outputs (exact file paths or artifacts)
     - Acceptance Criteria (each item must be verifiable)
     - Router Notes (which agent runs first; likely follow-on agents)

3) BUDGET
   - Author Allowed Context include lists:
     - Minimal, explicit paths (files/dirs) required to execute the capsule
     - Brief rationale per path
   - Set Context Budget (default <= 300 lines) and justify if higher.
   - If budget seems too tight, prepare a note to Context Warden.

4) VERIFY
   - Check that every referenced path exists or is marked as “to be created by <agent>”.
   - Turn each Acceptance point into a concrete check:
     - command to run (e.g., pnpm -C .sentinel validate:contracts)
     - file presence or diff
     - test name or sentinel path
   - Confirm provenance headers and ASCII-only formatting.

5) PACKAGE
   - Save capsule.md.
   - (Optional) Update /spec-index/index.json with capsule_id, title, primary agent.
   - (Optional) Write /router-notes/<capsule_id>.md summarizing start agent and handoffs.

6) HANDOFF
   - Tag Context Warden to lint Allowed Context and budgets.
   - Tag Verifier to ensure assertions/tests exist or to scaffold them.
   - Notify Router that the capsule is ready to schedule.

Notes:
- Keep capsules surgical. If the scope sprawls, split into multiple capsules.
- If Acceptance cannot be verified without adding tests, explicitly request a Verifier follow-up.
- If any behavior change is implied, state it and link the authorizing Decision-ID.
