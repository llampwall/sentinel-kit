# Router Log

Router selections are appended as JSONL files (one per capsule) under this directory. Each entry should include:

```json
{
  "timestamp": "2025-11-07T22:15:00Z",
  "capsule": ".specify/specs/004-capsule-gen/capsule.md",
  "leadAgent": "scribe",
  "requiredOutputs": ["docs/context/IMPLEMENTATION.md"],
  "acceptanceCriteria": ["Implementation doc updated"],
  "contextToMount": [".specify/specs/004-capsule-gen/capsule.md", ".sentinel/agents/scribe/**"],
  "notes": "Docs-only pass"
}
```

This log is for auditability only; it never replaces `DECISIONS.md`.
