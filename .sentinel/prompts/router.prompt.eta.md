<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0011 -->
<!--
  Eta template for Router prompts.
  Expected `it` shape:
    {
      router: { role: string, playbook: string },
      capsule: { path: string, content: string, allowedContext: string[] },
      agents: [{ id, name, rulesHash, summary, routingKeywords: string[] }]
    }
-->
<%~ it.router.role %>

<%~ it.router.playbook %>

## Capsule
- Path: <%= it.capsule.path %>
- Allowed Context:
<% it.capsule.allowedContext.forEach((ctx) => { %>
  - <%= ctx %>
<% }) %>

## Available Agents
<% it.agents.forEach((agent) => { %>
- **<%= agent.name %>** (`<%= agent.id %>`)
  - RulesHash: <%= agent.rulesHash %>
  - Summary: <%= agent.summary %>
  - Keywords: <%= agent.routingKeywords.join(", ") %>
<% }) %>

## Capsule Text
--- BEGIN CAPSULE ---
<%~ it.capsule.content %>
--- END CAPSULE ---

## Output Schema
```json
{
  "leadAgent": "<one of the agent ids above>",
  "requiredOutputs": ["String"],
  "acceptanceCriteria": ["String"],
  "contextToMount": ["String"],
  "notes": "Short rationale"
}
```

## Rules
1. Choose exactly one Lead Agent.
2. Copy Allowed Context paths from the capsule verbatim (no invented globs).
3. Respond with JSON only—no prose, code fences, or commentary.
4. If no agent fits, abort and request a capsule/agent update instead of guessing.
