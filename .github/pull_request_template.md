<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0018 -->
## Checklist
- [ ] Capsule updated or confirmed unchanged (include path)
- [ ] Decision logged via `uv run sentinel decisions append --author <agent> --scope <path> --decision "<summary>" --rationale "<why>" --outputs <files>`
- [ ] Sentinels run locally: `uv run sentinel sentinels run`
- [ ] Context linter: `uv run sentinel context lint`
- [ ] MCP smoke (optional, recommended): `uvx sentinel mcp smoke`

## Summary
Describe the change, linked tasks, and any follow-up required.

## Testing
Paste commands/output that prove the checklist above ran locally.
