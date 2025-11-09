<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.1 Decision=D-0011 -->
### Prompt renderer workflow

The Eta-based renderer lives in `.sentinel/scripts/orch/prompt-render.mjs`. Use it to hand capsules to the router and lead agents with the correct context and logging.

1. **Render prompts** from the repo root:
   ```bash
   pnpm --dir=.sentinel node scripts/orch/prompt-render.mjs \
     --mode router \
     --capsule .specify/specs/<slug>/capsule.md \
     [--output router.md]

   pnpm --dir=.sentinel node scripts/orch/prompt-render.mjs \
     --mode capsule \
     --capsule .specify/specs/<slug>/capsule.md \
     --agent builder \
     [--output builder.md]
   ```
   - `--output` writes the prompt to disk; omit it to stream to stdout.
   - Capsule paths are relative to repo root; pass absolute paths if running elsewhere.
2. **Validate router decisions** (optional but recommended) by supplying the router’s JSON file:
   ```bash
   pnpm --dir=.sentinel node scripts/orch/prompt-render.mjs \
     --mode router \
     --capsule .specify/specs/<slug>/capsule.md \
     --router-json ./router-output.json
   ```
   This enforces the JSON schema (leadAgent, requiredOutputs[], contextToMount[], notes) and appends an entry to `.sentinel/router_log/<timestamp>-<slug>.jsonl` with a hashed capsule path.
3. **Smoke-test** the end-to-end flow anytime the renderer changes:
   ```bash
   pnpm --dir=.sentinel node scripts/orch/prompt-render.smoke.mjs [capsule] [agent]
   ```
   The smoke script renders router, then capsule mode (defaults to `005-capsule-gen` + `builder`) and prints previews + prompt lengths.
4. **Tests**:
   ```bash
   pnpm --dir=.sentinel vitest run tests/orch/agents.test.ts tests/orch/prompt-render.test.ts
   ```
   These cover agent discovery, template rendering, router schema validation, log writes, and CLI flows.

Tips:
- Router logs are JSONL (one file per run). Each entry includes ISO timestamp, relative capsule path, a short hash, and the validated payload.
- Capsule prompts inherit Allowed Context directly from the capsule; if you see missing paths, update the capsule before re-rendering.
- Running with `--output` makes it easier to copy/paste prompts into external tools without losing formatting.
