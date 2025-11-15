# Sentinel Asset Mapping for `specify init --sentinel`

## Purpose

Task 8.1 requires a definitive list of Sentinel-specific assets that must land in every scaffold created with `specify init --sentinel`. This document is the hand-off contract between the SentinelKit repo and the Specify CLI implementation:

- **Source root** refers to this repository (`sentinel-kit`), the place `specify init --sentinel` will copy from.
- **Destination root** refers to the brand-new project the user is scaffolding.
- Only the assets listed below should be copied; anything omitted remains internal to the SentinelKit workspace.

## 1. Workspace & Toolchain Files

| Asset | Source Path | Destination | Notes |
| --- | --- | --- | --- |
| Root workspace config | `pyproject.toml` | `<project>/pyproject.toml` | Must include the SentinelKit dependency block (`sentinel` script, `[tool.uv.workspace] members = ["sentinelkit"]`, `[tool.uv.sources] sentinelkit = { workspace = true }`). Merge with scaffold template rather than replacing user metadata. |
| UV lockfile | `uv.lock` | `<project>/uv.lock` | Provides a fully locked dependency graph so `uv sync --locked` works on first bootstrap. |
| Toolchain pin | `.tool-versions` | `<project>/.tool-versions` | Keeps Python pinned (3.12.x). If the scaffold already has a `.tool-versions`, ensure the Python entry matches Sentinel requirements. |
| Make targets | `Makefile` | `<project>/Makefile` | Ships `bootstrap`, `sync`, `selfcheck`, `test`, and `lint` shortcuts that wrap the UV commands defined below. |
| Bootstrap helper | `scripts/bootstrap.py` | `<project>/scripts/bootstrap.py` | Used by contributors and CI; runs `uv sync`, `uv run sentinel selfcheck`, and `uv run pytest`. |

## 2. SentinelKit Python Package

| Asset | Source Path | Destination | Notes |
| --- | --- | --- | --- |
| SentinelKit package manifest | `sentinelkit/pyproject.toml` | `<project>/sentinelkit/pyproject.toml` | Keeps SentinelKit versioned as a workspace member. |
| SentinelKit library sources | `sentinelkit/sentinelkit/**` | `<project>/sentinelkit/sentinelkit/**` | Includes CLI entry points, contract/context/capsule modules, runbook utilities, MCP scaffolding, etc. Exclude `__pycache__` and other build artifacts when copying. |

## 3. `.sentinel/` Enforcement Tree

| Asset | Source Path | Destination | Notes |
| --- | --- | --- | --- |
| Agent roles & playbooks | `.sentinel/agents/**` | `<project>/.sentinel/agents/**` | Router/CapsuleAuthor/etc. Include ROLE/PLAYBOOK files so agent bundles stay in sync. |
| Context limits & helpers | `.sentinel/context/**` | `<project>/.sentinel/context/**` | JSON schemas + helper configs consumed by the Python context lint. |
| Contracts + fixtures | `.sentinel/contracts/**` | `<project>/.sentinel/contracts/**` | Versioned contract YAML plus fixtures that power `sentinel contracts validate`. |
| Docs template | `.sentinel/docs/IMPLEMENTATION.template.md` | `<project>/.sentinel/docs/IMPLEMENTATION.md` | Copy the new template (added in this task) and rename it to `IMPLEMENTATION.md` during scaffold creation. |
| Prompts | `.sentinel/prompts/**` | `<project>/.sentinel/prompts/**` | Canonical router/agent prompt markdown referenced by capsule + agent sync logic. |
| Router log seed | `.sentinel/router_log/**` | `<project>/.sentinel/router_log/**` | Provides the logging layout expected by the prompt renderer and slash commands. |
| Snippets | `.sentinel/snippets/**` | `<project>/.sentinel/snippets/**` | Markdown snippets used by README/UPSTREAM automation plus Task 5 sync utilities. |
| Status docs | `.sentinel/status/**` | `<project>/.sentinel/status/**` | Tracks dev handoffs + status updates for capsules. |
| Capsule template | `.sentinel/templates/capsule.md` | `<project>/.sentinel/templates/capsule.md` | Consumed by `sentinel capsule generate`. |

## 4. CI & Automation Assets

| Asset | Source Path | Destination | Notes |
| --- | --- | --- | --- |
| Sentinel CI workflow | `.github/workflows/sentinel-ci.yml` | `<project>/.github/workflows/sentinel-ci.yml` | Provides the OS matrix (Windows/Linux/macOS) that runs `uv sync --locked --dev`, `uv run sentinel selfcheck`, and pytest with JSON/JUnit artifacts. |

## 5. Exclusions (Do **not** copy)

- `.sentinel/node_modules/**`, `.sentinel/package.json`, `tsconfig.json`, the `vitest.config.*` files, and any other legacy Node/Vitest artifacts.
- Build caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`, `*.pyc`, `*.pyo`, `.DS_Store`, etc.).
- Development-only directories (`memory/`, `tmp_contract/`, `.vscode/`, `.idea/`, etc.) unless the scaffold explicitly expects them.

## 6. Bootstrap Command Contract

`specify init --sentinel` must run the following immediately after copying assets (fail-fast on non-zero exit codes):

1. `uv sync --locked --all-groups` (fall back to `uv sync --dev` if `--locked` fails because the lockfile was regenerated). Always run from the destination root.
2. `uv run sentinel selfcheck --root . --format pretty` to prove contracts/context/tests/capsule tooling works before returning control to the user.

Both commands should be invoked exactly as shown so cross-platform UV shims (`uv` on Unix, `uv.exe` on Windows) continue to work. Prefer `subprocess.run([...], check=True)` with explicit error handling that surfaces Rich panels to the caller.

## 7. Platform & Path Notes

- Always derive source paths via `Path(__file__).resolve().parent.parent` inside `specify_cli` so zipped/bundled installs locate the embedded Sentinel files.
- When copying to Windows destinations, ensure directories are created with `parents=True, exist_ok=True` and use binary-safe file streams (`open(..., "wb")`) for non-text assets if we later ship binaries.
- Command invocations should avoid shell=True; pass arguments as lists so quoting works uniformly on PowerShell, cmd, bash, and zsh.
- When writing `.sentinel/docs/IMPLEMENTATION.md`, ensure the file uses LF line endings so the runbook updater’s line-budget logic remains deterministic across OSes.

## 8. Next Steps for Task 8

This mapping is the foundation for Task 8.2+:

- Task 8.2 will implement the actual copy mechanism in `specify init --sentinel` using this inventory.
- Task 8.3+ will hook the bootstrap commands and slash-command gates; they should reference this document whenever a new asset is added.

Keep this file updated whenever future tasks add or remove Sentinel assets so `specify init --sentinel` stays turnkey.
