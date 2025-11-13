<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0010 -->
### Capsule workflow

Capsules turn a Spec-Kit feature (`.specify/specs/<slug>`) into a router-ready hand-off with explicit Allowed Context.

1. Start from `.sentinel/templates/capsule.md`. The Typer capsule generator will copy this layout automatically; until it lands you can duplicate the template directly.
2. Keep the Spec-Kit artifacts (`spec.md`, `plan.md`, `tasks.md`) aligned with the capsule content. Capsule Task 5 lives in `.specify/specs/005-capsule-gen`.
3. Review the generated `.specify/specs/<slug>/capsule.md` and keep it under the 300-line budget. The Python Allowed Context helper auto-includes `.sentinel/context/**` so the router only mounts shared context.
4. Run the context linter after every capsule edit:
   ```bash
   uv run sentinel context lint --strict --sync-docs
   ```
   - `--capsule path/to/capsule.md` limits the run to the edited capsule(s).
   - `--sync-docs` refreshes the `SENTINEL:CAPSULES` block in `README.md` via the md-surgeon helper so docs track the latest guidance.
5. Enable the git hook (`git config core.hooksPath .husky`) if your workflow frequently touches `.specify/specs/*/capsule.md`, `.sentinel/context/**`, or prompt files. The hook re-runs the linter before commits proceed.
6. Re-run sentinel tests whenever capsule or context code changes:
   ```bash
   uv run pytest -q tests/context
   ```
   Add targeted sentinel fixtures alongside regression tests under `tests/context/` to capture past failures.
7. When you update capsule docs, edit `.sentinel/snippets/capsules.md` and re-run `uv run python -m sentinelkit.scripts.md_surgeon --file README.md --marker=SENTINEL:CAPSULES --content .sentinel/snippets/capsules.md` (or pass `--sync-docs` to the linter) so README stays in sync.
