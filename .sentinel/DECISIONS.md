<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0004 -->

# Decisions Ledger

## NEXT_ID
D-0005

## Format
- ID: D-####  
- Date: YYYY-MM-DD  
- Author: <you/agent>  
- Scope: <files or subsystem>  
- Decision: <what we decided>  
- Rationale: <why>  
- Supersedes: <ID or none>

## Log

ID: D-0002
Date: 2025-11-06
Author: Jordan
Scope: .sentinel/contracts/users.v1.yaml
Decision: Clarify users.v1 is an array of user objects (not a single object)
Rationale: Align contract with real fixture shape; unblock validation and unit test
Supersedes: none

ID: D-0003
Date: 2025-11-06
Author: Scribe
Scope: src/users_consumer.mjs; scripts/contracts/validate.mjs; scripts/mcp/*.mjs; tests/**
Decision: Introduce MCP server `contract.validate` and document code
Rationale: Document provenance, explain call flows, and expose validation via MCP tooling
Supersedes: none

ID: D-0004
Date: 2025-11-07
Author: Builder
Scope: .sentinel/scripts/orch/prompt-render.mjs; README.md; .sentinel/DECISIONS.md
Decision: Introduce minimal orchestrator CLI + docs to render router/capsule prompts locally
Rationale: Auto-discover agents, mount their context at runtime, and document the workflow for Codex users
Supersedes: none
