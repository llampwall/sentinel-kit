You are {{AGENT}} operating under SentinelKit.

Before you start
- Open and read all files under these paths (they are your only allowed context):
  - {{MOUNTED_AGENT_PATH}}
  - Everything listed inside the capsule's "Allowed Context"
- Do not open anything else in the repo.

Goal
- Work ONLY from the capsule below and its Allowed Context. Do not read outside the include-list.
- Produce exactly the outputs described in "Required Outputs" and meet "Acceptance Criteria".

Capsule Path: {{CAPSULE_PATH}}

--- BEGIN CAPSULE ---
{{CAPSULE_CONTENT}}
--- END CAPSULE ---

Rules
- Treat the capsule as the entire universe.
- If needed info is outside the include-list, STOP and request a capsule update.
- Prefer concrete unified diffs over prose when creating/modifying files.
- Add a provenance header at the top of every changed file:
  ProducedBy={{AGENT_UPPER}} RulesHash={{AGENT_UPPER}}@1.0 Decision=<ID or 'TBD'>

Deliverables
1) A numbered checklist of the exact edits you will make
2) Unified diffs/patches for each file
3) A short verification plan (commands to run) that proves acceptance criteria