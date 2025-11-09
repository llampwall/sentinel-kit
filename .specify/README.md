## Capsule Workflow within Spec-Kit


<!-- SENTINEL:PROMPT-RENDER:start -->
<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.1 Decision=D-0011 -->
### Prompt renderer workflow

The Eta-based renderer lives in `.sentinel/scripts/orch/prompt-render.mjs`. Use it to hand capsules to the router and lead agents with the correct context and logging.

- Before rendering, the CLI now lints the capsule's Allowed Context via `pnpm --dir=.sentinel context:lint`. Invalid include lists (missing files, forbidden paths, or empty sections) abort the render with actionable errors, so fix the capsule before retrying.

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
<!-- SENTINEL:PROMPT-RENDER:end -->


Sentinel capsules are generated from the Spec-Kit artifacts under `.specify/specs/<slug>/`.
After `/speckit.specify`, `/speckit.plan`, and `/speckit.tasks` finish, the feature
directory contains `spec.md`, `plan.md`, and `tasks.md`. Use those three files to author
the capsule that routers and agents will consume.

### Template

- The canonical capsule template lives at `.sentinel/templates/capsule.md`.
- It documents the required sections (Goal, Required Outputs, Acceptance Criteria,
  Allowed Context, Router Notes) and the `{{TOKEN}}` placeholders used by the generator.
- Manual capsules can be created by copying that template and filling in each section,
  but the recommended flow is to let the generator hydrate it automatically.

### Generator CLI

Run the generator from the repo root (it executes inside `.sentinel/` automatically):

```bash
pnpm -C .sentinel capsule:create --spec .specify/specs/<slug> --decision D-XXXX
```

- `--spec` points at the feature folder created by Spec-Kit.
- `--decision` must match the next ID in `.sentinel/DECISIONS.md`.
- Optional `--agent` and `--rulesHash` override the ProducedBy header.

The CLI reads the feature’s spec/plan/tasks, applies the template, hashes a capsule ID,
auto-populates Allowed Context (including `.sentinel/context/**`), enforces the 300-line
budget, and writes `.specify/specs/<slug>/capsule.md`.

### Validation

Before handing the capsule to another agent:

```bash
pnpm -C .sentinel vitest run tests/capsule-create.test.ts
pnpm -C .sentinel test:sentinels -- --testNamePattern capsule-context
```

Those suites ensure the generator output stays deterministic and the Allowed Context
linter rejects missing paths.

### speckit.tasks Integration

The `/speckit.tasks` command now assumes each feature directory has an accompanying
capsule. After refining the tasks, re-run the capsule generator so the newest Required
Outputs/Acceptance Criteria are reflected. Include the capsule path in PRDs, Task Master
entries, and router prompts so downstream agents always operate with the approved
include-list.
