## Capsule Workflow within Spec-Kit

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
