Router role content.

Router playbook content.

## Capsule
- Path: specs/sample/capsule.md
- Allowed Context:
  - README.md
  - src/example.py

## Available Agents
- **Builder** (`builder`)
  - RulesHash: BUILDER@1.0
  - Summary: Executes capsule tasks inside Allowed Context.
  - Keywords: build, impl
- **Router** (`router`)
  - RulesHash: ROUTER@1.0
  - Summary: Assigns lead agents and enforces capsule context.
  - Keywords: route

## Capsule Text
--- BEGIN CAPSULE ---
# Fixture Capsule

## Allowed Context
- README.md
- src/example.py

## Goal
- Keep routers honest.
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
