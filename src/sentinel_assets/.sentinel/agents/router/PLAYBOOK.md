# Router - Playbook

## Checklist
- Capsule read once; Allowed Context copied verbatim.
- Exactly one leadAgent.
- requiredOutputs mirror capsule wording (files, diffs, MCP calls).
- acceptanceCriteria are actionable verifications.
- contextToMount = capsule list + .sentinel/agents/<agent>/** only.
- Router log entry appended with ts, rulesHash, capsule, response, decisionId, producedBy.

## Flow
1) Load agents
   - Parse .sentinel/agents/*/agent.json to understand scope and RulesHash.

2) Evaluate fit
   - Match capsule requirements to routing_keywords/responsibilities for a single best agent. If the capsule’s Router Notes name a preferred starting agent, honor that unless it conflicts with Allowed Context or the agent’s charter.

3) Draft JSON
   - Keep arrays small; include brief notes if trade-offs exist.

4) Emit response
   - Reply with JSON only; let prompt-render hand the baton to the chosen agent.

5) Verify prompt
   - Ensure the rendered agent prompt lists the correct Allowed Context and provenance instructions.
   - Confirm no transitive mounts were added.

## Escalate When
- Capsule lacks the files needed to complete the task.
- No agent’s charter matches the work.
- Required outputs would violate current RulesHash or repo policies (e.g., would exceed Allowed Context or break context budgets).
