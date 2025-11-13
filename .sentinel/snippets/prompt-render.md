<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.1 Decision=D-0011 -->
### Prompt renderer workflow

The Python renderer now lives under `sentinelkit.prompt.render` and is exposed via the Typer CLI (`uv run sentinel prompts render`). Use it to hand capsules to the router and lead agents with the correct context, logging, and Allowed Context validation.

- Before rendering, the CLI automatically lints the capsule via `sentinel context lint`. Invalid include lists (missing files, forbidden paths, or empty sections) abort the render with actionable errors—fix the capsule before retrying.

1. **Render prompts** from the repo root:
   ```bash
   uv run sentinel prompts render \
     --mode router \
     --capsule .specify/specs/<slug>/capsule.md \
     [--output router.md]

   uv run sentinel prompts render \
     --mode capsule \
     --capsule .specify/specs/<slug>/capsule.md \
     --agent builder \
     [--output builder.md]
   ```
   - `--output` writes the prompt to disk; omit it to stream to stdout.
   - Capsule paths are relative to repo root; pass absolute paths if running elsewhere.
2. **Validate router decisions** (optional but recommended) by supplying the router’s JSON file:
   ```bash
   uv run sentinel prompts render \
     --mode router \
     --capsule .specify/specs/<slug>/capsule.md \
     --router-json ./router-output.json
   ```
   This enforces the router JSON schema (leadAgent, requiredOutputs[], contextToMount[], notes) and appends an entry to `.sentinel/router_log/<timestamp>-<slug>.jsonl` with a hashed capsule path.
3. **Smoke-test** the end-to-end flow anytime the renderer changes by rendering both router and capsule prompts (with `--output`) and spot-checking the log file.
4. **Tests**:
   ```bash
   uv run pytest -q tests/prompts/test_renderer.py
   ```
   These cover agent discovery, template rendering, router schema validation, log writes, and CLI flows.

Tips:
- Router logs are JSONL (one file per run). Each entry includes ISO timestamp, relative capsule path, a short hash, and the validated payload.
- Capsule prompts inherit Allowed Context directly from the capsule; if you see missing paths, update the capsule before re-rendering.
- Running with `--output` makes it easier to copy/paste prompts into external tools without losing formatting.
