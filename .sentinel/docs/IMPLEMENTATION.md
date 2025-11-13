# Implementation Notes

## Task 1.1 Summary

- `.taskmaster/docs/sentinel_python_integration_rpg.md` defines the Python-only migration: uv workspace, sentinelkit beside specify-cli, and single-command validation.
- `.taskmaster/tasks/tasks.json` Task 1 / Subtask 1.1 requires one `pyproject.toml` that exposes both packages plus a verification step of `uv pip show sentinelkit specify-cli`.
- The repo now uses a uv workspace: `sentinelkit/` has its own `pyproject.toml`, `[tool.uv.workspace] members = ["sentinelkit"]`, and `[tool.uv.sources] sentinelkit = { workspace = true }`.
- Because sentinelkit is a workspace dependency, `uv pip install -e .` (or `uv sync`) installs both CLIs in editable mode without environment toggles; `uv pip show sentinelkit specify-cli` now points at the shared clone.

## Task 1.2 Summary

- `.tool-versions` now pins **only** Python 3.12.2, eliminating the Node/pnpm entries and making the uv bootstrap authoritative.
- `uv sync` produced a committed `uv.lock`, so every worktree resolves dependencies identically.
- `sentinelkit/sentinelkit/__init__.py` exposes `__version__`, `VersionInfo`, and helper functions (`get_version`, `get_version_info`, `version_components`) so downstream code can inspect the package version immediately.
- Validation command from the task (`uv run python -c "import sentinelkit; print(sentinelkit.__version__)"`) succeeds on a clean checkout thanks to the new exports.

## Task 1.3 Summary

- Scaffolded the SentinelKit namespace layout (`contracts/`, `context/`, `capsule/`, `prompt/`, `cli/`, `utils/`, `scripts/`, and `tests/`) with placeholder modules that currently raise `NotImplementedError`.
- Added the Typer-based CLI entry point (`sentinelkit/cli/main.py`) along with contract/context/decision/MCP subcommand stubs, plus the published `sentinel` script via `[project.scripts] sentinel = "sentinelkit.cli.main:app"`.
- Updated `sentinelkit/pyproject.toml` to depend on Typer so the CLI resolves in isolation or via the workspace install.
- Verified the task’s acceptance criteria with `uv run python -c "import sentinelkit.cli.main"` and `uv run sentinel --help`.

## Task 1.4 Summary

- Authored `scripts/bootstrap.py`, which sequentially runs `uv sync`, `uv run sentinel selfcheck`, and `uv run pytest -q`.
- Replaced the legacy pnpm-based Makefile with Python-only targets (`bootstrap`, `sync`, `selfcheck`, `test`, `lint`) and a `PYTHON` override for cross-shell use.
- Added a placeholder `sentinel selfcheck` Typer command plus a minimal pytest smoke test to keep the bootstrap green.
- Declared dev dependencies via `[dependency-groups] dev = ["pytest", "ruff"]` so `uv sync` brings in the tooling automatically, and validated `python scripts/bootstrap.py`.

## Task 1.5 Summary

- Replaced `.github/workflows/sentinel-kit.yml` with the uv-native `sentinel-ci.yml` workflow that runs on Ubuntu, macOS, and Windows.
- Each job installs Python 3.12 via `actions/setup-python`, installs uv with `astral-sh/setup-uv`, runs `uv sync --locked --dev`, `uv run sentinel selfcheck --verbose`, and `uv run pytest -q --junitxml=...`, uploading artifacts for every platform.
- README and runbook now reference the new workflow name and badge.

## Task 1.6 Summary

- README now describes the uv-only bootstrap (`uv sync && python scripts/bootstrap.py` / `make bootstrap`), links to the new CI badge, and replaces pnpm guidance in the MCP/Capsule sections with the incoming Python CLI.
- `docs/local-development.md` gained a SentinelKit bootstrap section so local contributors know to run the new script.
- Added `tests/smoke/test_imports.py`, a smoke test that imports every `sentinelkit` module, satisfying the new pytest requirement.
- `uv run pytest` passes after the documentation updates and new smoke test.

## Task 2.1 Summary

- Rebuilt the Typer root (`sentinelkit/cli/main.py`) with a callback that sets shared `--root` and `--format` options and exposes the required namespaces (`contracts`, `context`, `capsule`, `prompts`, `sentinels`, `decisions`, `runbook`, `mcp`, and `selfcheck`).
- Added placeholder modules for each namespace plus a shared `cli/state.py` helper that stores the resolved root/output format.
- The CLI still surfaces placeholders, but `uv run sentinel --help` now shows the full command tree and options.

## Task 2.2 Summary

- Extended `cli/state.py` to capture environment metadata (`is_ci`, platform, python version) alongside the shared root/output format so all commands have consistent context.
- Implemented normalized error helpers in `sentinelkit/utils/errors.py` (dataclass payloads, serialization helpers, and enriched `SentinelKitError`).
- Added `cli/executor.py`, a threaded check runner that gathers structured `CheckResult` objects with Rich status updates; this will power the real selfcheck aggregator.

## Task 2.3 Summary

- Implemented the `sentinel selfcheck` command using the shared executor: it fans out named checks (currently placeholders) and aggregates their status.
- Pretty mode prints a Rich table, `--format json` emits `{"ok": bool, "environment": {...}, "checks": [...]}` so Specify CLI can parse results later.
- The command now exits non-zero if any check fails and honors `--verbose` to suppress the status spinner.

## Task 2.4 Summary

- Added `tests/cli/test_selfcheck.py`, which uses Typer's `CliRunner` to cover pretty/json success cases plus failure exit-code propagation.
- Tests monkeypatch `_build_checks` to simulate stubbed checks and assert structured JSON payloads, ensuring the CLI plumbing is verified before real check implementations arrive.

## Task 2.5 Summary

- `specify check` now shells out to the Python selfcheck via the new `run_sentinel_selfcheck` hook, surfacing the same Rich output/errors as the standalone CLI.
- Updated README and local-development docs to explain the selfcheck flow and mention that `specify check` delegates to `uv run sentinel selfcheck` (including `--format json` guidance for automation).

## Task 3.2 Summary

- Added `sentinelkit/contracts/loader.py`, which caches YAML schemas, provides deterministic `iter_contract_fixtures`, and enforces sorted ordering for both schemas and fixtures.
- Declared new dependencies (`pyyaml`, `jsonschema`) in `sentinelkit/pyproject.toml` so future contract validation work has the required libraries.
- Introduced `tests/contracts/test_loader.py` to cover cache behaviour, force reload, fixture ordering, and path filtering—matching the legacy Node validator semantics.

## Task 3.3 Summary

- Implemented the contract validation core (`sentinelkit/contracts/api.py`) using the loader plus `jsonschema` Draft 2020 validators with ProducedBy enforcement.
- Added unit tests (`tests/contracts/test_api.py`) covering success/failure cases, ProducedBy violations, and the `ValidationResult` serialization helpers.

## Task 3.5 Summary

- Added CLI snapshot coverage (`tests/contracts/test_cli_snapshot.py`) that runs `uv run sentinel contracts validate --format json` against sample fixtures and compares the sanitized JSON output to a stored golden (`tests/contracts/snapshots/sample_full.json`).
- Ensured snapshot normalization replaces absolute paths with `{{ROOT}}` placeholders so future runs remain deterministic across environments.

## Task 4.1 Summary

- Replaced the stubbed Allowed Context discovery module with a full implementation in `sentinelkit/context/allowed_context.py`, including `AllowedContextEntry` dataclass metadata, repo-root auto-discovery, duplicate suppression, deterministic ordering, and line-count bookkeeping.
- Added guardrail helpers (`normalize_include`, `assert_include_exists`) that raise structured `AllowedContextError`s on root escapes, missing files, or malformed entries, ensuring capsules can only include files inside the repo.
- Introduced fixture-backed pytest coverage (`tests/context/test_allowed_context.py` + `tests/context/fixtures/allowed_context/**`) to verify deterministic discovery, deduplication, and error handling.

## Task 4.2 Summary

- Implemented the Python context limit schema loader in `sentinelkit/context/limits.py` using dataclasses (`ContextRule`, `CapsuleRule`, `ContextLimits`), JSON Schema validation (Draft 7), and normalized path handling with caching.
- The loader now supports YAML/JSON configs, override-specific line budgets, warning-threshold validation, and exposes `to_dict()` for future diagnostics/JSON output.
- Added fixtures and tests (`tests/context/fixtures/context_limits/context-limits.json`, `tests/context/test_limits.py`) covering artifact parsing, default threshold behavior, and validation failures.

## Task 4.3 Summary

- Built the Allowed Context linter in `sentinelkit/context/lint.py`, mirroring the legacy JS behavior: collects artifact targets via the limits config, enforces per-file line budgets/overrides, and validates capsule Allowed Context lists (missing section, invalid/missing include, forbidden paths, duplicates).
- Wired the Typer CLI (`sentinel context lint`) to the new engine with support for `--capsule`, `--strict`, `--config`, `--schema`, and `--format json`, including structured error reporting that integrates with the global CLI context.
- Added capsule fixtures + pytest suite (`tests/context/fixtures/capsules/*.md`, `tests/context/fixtures/context_limits/lint-config.json`, `tests/context/test_context_lint.py`) plus ran `uv run pytest -q tests/context` to confirm coverage for diagnostics, strict-mode exit gating, and repo-root escaping.

## Task 4.4 Summary

- Rebuilt `.sentinel/context/fixtures` with reusable capsules (`line-299/300/301`, escape, forbidden, duplicate, missing-context, missing-include) plus a dedicated fixture config (`context-limits.fixture.json`) so both humans and tests can quickly demonstrate the 300-line guardrail and Allowed Context rules.
- Added regression tests in `tests/context/test_context_fixtures.py` that run the Python linter against the new fixtures, covering near-limit warnings, hard failures at 301 lines, missing Allowed Context sections, forbidden/duplicate entries, and deterministic diagnostic ordering.
- Tweaked the line-count helper in `sentinelkit/context/lint.py` to mirror the Allowed Context counter (no off-by-one when files end with `\n`) and ran `uv run pytest -q tests/context` to validate the refreshed fixtures and suite (now 19 tests).

## Task 4.5 Summary

- Ported the md-surgeon workflow to Python (`sentinelkit/scripts/md_surgeon.py`) with parity features (marker replacement, heading/append modes, code-fence validation, `.bak` backups, CLI entry point) plus a pytest suite in `tests/scripts/test_md_surgeon.py`.
- Wired `sentinel context lint` with a `--sync-docs` flag that reuses the new md-surgeon helper to refresh the README `SENTINEL:CAPSULES` block from `.sentinel/snippets/capsules.md`, ensuring documentation stays aligned whenever lint runs.
- Updated `.sentinel/snippets/capsules.md` and the corresponding README section to reflect the Python workflow (`uv run sentinel context lint --strict --sync-docs`, pytest regressions, md-surgeon invocation), keeping capsule guidance consistent with the new tooling.

## Task 5.1 Summary

- Audited the legacy Node capsule + prompt toolchain:
  - `.sentinel/scripts/capsule-create.mjs` remains the only implementation that parses spec/plan/tasks, hashes capsules, enforces the 300-line budget, and writes `capsule.md`. Python exposes only stubs (`sentinelkit/capsule/generator.py`, `cli/capsule.py`), so the generator, template renderer, and ProducedBy header logic must be ported wholesale.
  - `.sentinel/scripts/orch/prompt-render.mjs` and `orch/agents.mjs` load agent metadata, validate router payloads, render Eta templates, and write router logs. No Python equivalent exists yet (`sentinelkit/prompt/**` and `cli/prompts.py` are placeholders), meaning router/capsule prompt rendering still depends on Node + Eta.
  - Snippet workflows still rely on `.sentinel/snippets/*.md` plus md-surgeon markers in README/UPSTREAM/etc.; only the capsule snippet is wired to the new Python md-surgeon.
- Identified priorities for upcoming subtasks:
  1. Port capsule template rendering + hashing into Python, using the new Allowed Context + limits modules and exposing the generator via Typer/CLI + tests.
  2. Reimplement agent discovery, prompt template rendering, and router logging in Python (Eta replacement TBD) and surface them through `sentinel prompts render`.
  3. Generalize the md-surgeon bridge so other snippets (workflow badge, MCP validator, decision log) can be refreshed from Python commands, keeping docs in sync after lint/prompt/capsule runs.

## Task 5.2 Summary

- Implemented the capsule generator in Python, covering spec/plan/tasks parsing, SHA-based capsule IDs, ProducedBy header rendering, Allowed Context seeding via the discovery module, template replacement, and the 300-line budget guard (`sentinelkit/capsule/generator.py`).
- Exposed the generator through `sentinel capsule generate` with `--spec`, `--decision`, `--agent`, `--rules-hash`, and `--dry-run`, returning structured errors for missing files or line-budget violations.
- Added pytest coverage (`tests/capsule/test_generator.py`) with fixture templates proving deterministic output, Allowed Context injection, and enforcement of the line cap.

## Task 5.3 Summary

- Ported the Eta prompt renderer into Python using Jinja templates (`sentinelkit/prompt/templates/*.md.j2`) plus a new `PromptRenderer` that loads agents, validates capsules via the Python linter, renders router/agent prompts, and writes router logs (`sentinelkit/prompt/render.py`, `sentinelkit/prompt/agents.py`).
- Updated the Typer CLI (`sentinelkit/cli/prompts.py`) to support `uv run sentinel prompts render --mode {router|capsule}` with options for `--capsule`, `--agent`, `--output`, and `--router-json`, surfacing structured errors on lint/template failures.
- Added pytest coverage (`tests/prompts/test_renderer.py`) that exercises router/agent prompt rendering and router log creation with temporary capsules, agents, and context-limit configs.

## Task 5.4 Summary

- Added a reusable snippet sync module + CLI (`sentinelkit/scripts/snippets.py`, `sentinelkit/cli/snippets.py`) that reuses the Python md-surgeon helper to refresh README/UPSTREAM markers (workflow badge, MCP validator, capsules, decision log, prompt renderer, upstream decision). Context lint’s `--sync-docs` flag now delegates to the same helper instead of duplicating logic.
- Introduced shared path utilities (`sentinelkit/utils/paths.py`) and wired `sentinel context lint` to use them for glob normalization, keeping future modules consistent.
- Updated `.sentinel/snippets/prompt-render.md` + README marker (`SENTINEL:PROMPT-RENDER`) to document the new `uv run sentinel prompts render` workflow, and added pytest coverage for snippet syncing (`tests/scripts/test_snippet_sync.py`).

## Task 5.5 Summary

- Hooked capsule/prompt/snippet workflows into the Typer CLI with end-to-end smoke tests (`tests/cli/test_capsule_prompts_snippets.py`), ensuring `sentinel capsule generate`, `sentinel prompts render`, and `sentinel snippets sync` match the legacy behavior.
- Synced the capsule + prompt README snippets via the new CLI utilities so docs always reflect the Python commands.

## Task 5.6 Summary

- Added golden snapshot coverage for the capsule generator (`tests/capsule/test_generator_snapshot.py`) driven by fixtures under `tests/fixtures/capsule_snapshot/**`.
- Captured router/agent prompt outputs in fixtures (`tests/fixtures/prompts_snapshot/**`) and enforce them via `tests/prompts/test_renderer.py`.
- Expanded the CLI test suite to assert the new commands succeed in temp workspaces, providing regression protection for generator, renderer, and snippet flows.

## Task 6.1 Summary

- Ported the sentinel regression suites to pytest:
  - `tests/sentinels/test_capsule_context.py` mirrors the legacy Vitest coverage for Allowed Context helpers, ensuring requested seeds are included while maintainer notes stay excluded and missing paths raise errors.
  - `tests/sentinels/test_users_email_format.py` loads the `users.v1` fixture via the Python contract validator and guards the RFC email regex regression.
- Folded the sentinel tests into the focused pytest run (`uv run pytest -q tests/sentinels …`), giving us a Python-native sentinel suite ready for future CLI wrappers.

## Task 6.2 Summary

- Added shared pytest fixtures (`tests/conftest.py`) for `repo_root`, `contract_loader`, and `contract_validator` so sentinel tests reuse a single loader/validator without duplicating setup.
- Refactored the sentinel suites to consume the fixtures, keeping tests lean and deterministic while paving the way for additional sentinel modules.

## Task 6.4 Summary

- Wired CI and selfcheck to the new Python sentinel runner: `sentinelkit/cli/sentinels.py` now exposes a reusable helper consumed by both `sentinel sentinels run` and the selfcheck “sentinels” check, while `.github/workflows/sentinel-kit.yml` executes the CLI and uploads JSON/JUnit artifacts.
- Added CLI coverage in `tests/cli/test_cli_commands.py` to assert capsule/prompt/snippet flows plus sentinel run + selfcheck JSON output, ensuring the new artifacts exist and contain the expected metadata.
- Updated `.sentinel/tests/sentinels/README.md` to document the `uv run sentinel sentinels run` workflow alongside the legacy pnpm commands.

## Task 7.1 Summary

- Ported the Node decision-log workflow into Python (`sentinelkit/cli/decision_log.py`) with dataclasses for payloads/results, NEXT_ID parsing, deterministic entry rendering, ProducedBy snippet builders, and cross-platform file locking via `portalocker`.
- Added dry-run/preview support so CI can request `--dry-run --output preview.md` without mutating `DECISIONS.md`, while standard appends atomically bump `NEXT_ID`, write the new entry, and emit snippets that include the current git short hash.
- Created regression fixtures + pytest coverage (`sentinelkit/tests/fixtures/DECISIONS.sample.md`, `tests/test_decision_log.py`) that validate ID bumping, ledger mutation, dry-run preview behavior, and required-field validation.

## Task 7.2 Summary

- Implemented the runbook utilities package (`sentinelkit/runbook/updater.py`) with a section registry (Current Enforcement Surface, Execution Flow, Known Gaps, CI Workflow, Stack Context), deterministic placeholders, and note formatting helpers (timestamp + author metadata).
- `RunbookUpdater.append(...)` now auto-seeds missing sections inside `.sentinel/docs/IMPLEMENTATION.md`, removes the “no entries yet” placeholder for the targeted section, appends normalized notes, and supports dry-run previews via `--output` paths for CI.
- Added pytest coverage (`tests/test_runbook_updater.py`) validating section creation, placeholder removal, dry-run previews, and unknown-section error handling.

## Task 7.3 Summary

- Wired Typer commands for `sentinel decisions append` and `sentinel runbook append`, pulling from the shared CLI context so automation (e.g., `/speckit.clarify`) can log decisions and runbook notes relative to `--root` with consistent JSON/pretty output and structured error handling.
- Decisions CLI now shells out to the Python ledger core with support for scope/outputs lists, optional ProducedBy overrides, dry-run previews, and snippet emission; runbook CLI handles section slug validation, ISO8601 timestamp overrides, and preview files for CI diffs.
- Added integration coverage via `tests/test_cli_decisions_runbook.py`, ensuring both commands mutate their respective artifacts (or dry-run) and emit the ProducedBy snippet + runbook entries expected by downstream automation.

## Task 7.4 Summary

- Expanded the decision ledger unit tests to include ProducedBy snippet assertions, missing-output validation, and lock contention handling that now surfaces a `decision.lock_timeout` error when another writer holds the `.lock` file (`tests/test_decision_log.py`).
- Added CLI-focused regression tests that exercise `sentinel decisions append --dry-run --output preview.md` and the runbook counterpart to guarantee ledgers/runbooks remain untouched during previews while JSON output flags `dry_run: true` (`tests/test_cli_decisions_runbook.py`).
- Ensured runbook updater coverage still verifies placeholder removal/deterministic inserts while the CLI suite now covers both standard and dry-run flows, satisfying the integration-test requirement for Task 7.4.

## Task 8.1 Summary

- Authored `.sentinel/docs/sentinel_asset_mapping.md`, a source-to-destination checklist covering every Sentinel asset that `specify init --sentinel` must copy (workspace files, SentinelKit package, `.sentinel/**`, CI workflow) plus the exclusions and bootstrap command contract (`uv sync --locked`, `uv run sentinel selfcheck`).
- Added `.sentinel/docs/IMPLEMENTATION.template.md`, a clean runbook template that the scaffold can rename to `IMPLEMENTATION.md`, pre-populated with the placeholders expected by `sentinel runbook append`.
- Document now captures per-platform notes (Path handling, uv invocation) so later subtasks can wire the copy/bootstrapping logic without re-auditing the repo.

## Task 8.2 Summary

- Extended `specify init` with a `--sentinel` flag that triggers the new `apply_sentinel_scaffold` helper: it copies every mapped asset (workspace files, SentinelKit package, `.sentinel/**`, CI workflow, runbook template) from the toolchain repo into the freshly scaffolded project (`src/specify_cli/__init__.py:115`), then runs `uv sync` (with graceful fallbacks) and `sentinel selfcheck` from the project root so contributors land on a green workspace automatically.
- Added progress tracking + Rich messaging for the Sentinel steps (`sentinel-copy`, `sentinel-uv`, `sentinel-selfcheck`) so operators can see exactly which phase is running; failures bubble up with actionable guidance (missing uv, selfcheck errors, etc.).
- Created pytest coverage in `tests/specify_cli/test_sentinel_scaffold.py` that exercises `apply_sentinel_scaffold` in a tmpdir, asserting that key files (pyproject, scripts/bootstrap.py, sentinelkit package, `.sentinel/docs/IMPLEMENTATION.md`, CI workflow) land in the destination while the uv/selfcheck runners are invoked.

## Known Gaps

- Placeholder modules still raise `NotImplementedError`; future subtasks will fill in the actual enforcement logic.
- README/CI/docs continue to describe the legacy Node workspace; updates remain scheduled for upcoming work.
