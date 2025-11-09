# Capsule Automation for Task 5

## Goal
SentinelKit capsules must capture Task 5 (template, generator CLI, Allowed Context enforcement) so routers can mount exactly the files required for provenance-safe automation. The capsule should summarize the work, the deliverables, and the acceptance bullets that currently live in the developer handoff doc.

## Rationale
- Capsule automation unlocks deterministic router flows and constrains Codex agents to the audited include list.
- Task 5 spans docs, CLIs, and sentinel suites; capturing that scope in one capsule keeps provenance tight.
- Context deduplication prevents accidental repo-wide reads while still surfacing `.sentinel/context` background notes.
