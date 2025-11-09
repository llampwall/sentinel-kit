<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0018 -->
## Checklist
- [ ] Capsule updated or confirmed unchanged (include path)
- [ ] Decision added via `node .sentinel/scripts/decision-log.mjs`
- [ ] Sentinels run locally: `pnpm --dir=.sentinel vitest run --config vitest.config.sentinel.ts --reporter=json`
- [ ] Context linter: `pnpm --dir=.sentinel context:lint`
- [ ] MCP smoke (optional, recommended): `pnpm --dir=.sentinel mcp:sentinel-run:smoke`

## Summary
Describe the change, linked tasks, and any follow-up required.

## Testing
Paste commands/output that prove the checklist above ran locally.
