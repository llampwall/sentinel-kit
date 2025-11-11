# PRD (RPG) — Sentinel‑Kit: Python‑Only Integration into Spec‑Kit (Windows/Linux/macOS)

> **Standard:** Task Master PRD + RPG format (author this file under `.taskmaster/docs/sentinel_python_integration_rpg.md` and parse with `task-master parse-prd`).

<overview>
## Problem Statement
Sentinel‑Kit currently ships Node-based utilities that complicate a Python‑first Spec‑Kit workflow and create brittle onboarding (Windows path quirks, pnpm config, split toolchains). We need Sentinel‑Kit to be **pure Python**, integrated end‑to‑end into Spec‑Kit’s flow and scaffolded directly by the **Specify CLI**. After initialization, a fresh clone on Windows/Linux/macOS must run a single bootstrap and pass all gates (contracts, context checks, sentinel tests, MCP smokes) with no Node.js, pnpm, or PowerShell dependencies.

## Target Users
- Spec‑Kit adopters who want a zero‑drama, Python‑native enforcement layer.
- Maintainers who need deterministic local setup and CI across OSes.
- AI‑assisted workflows (Codex/Cursor/Claude Code) that rely on Spec‑Kit’s `/speckit.*` flow and expect consistent gates.

## Success Metrics
- Fresh scaffold via `specify init --sentinel` → one Python bootstrap → green on Win/Linux/macOS.
- **No `node_modules`, no pnpm, no PowerShell**; a single Python toolchain via **uv**.
- `/speckit.*` commands run Sentinel gates automatically; failures are actionable.
- Parity: Python validators match legacy outputs (where applicable); Node enclave fully removed.
</overview>

<functional-decomposition>
## Capability Tree

### Capability: Python Enforcement Primitives
Replace JS tools with Python CLIs and libraries.

#### Feature: Contract Validation (Python)
- **Description**: Validate fixtures against versioned contracts via a Python CLI and MCP server.
- **Inputs**: `sentinel/contracts/*.yaml`, `sentinel/contracts/fixtures/**`.
- **Outputs**: JSON/pretty report; non‑zero exit on failure.
- **Behavior**: Pydantic/JSONSchema or Yamale-based schema validation; deterministic ordering; machine‑readable errors.

#### Feature: Sentinel Tests (Python)
- **Description**: Sentinel regression suites (pytest) encoding past bugs.
- **Inputs**: Fixtures + adapters under `tests/sentinels/**`.
- **Outputs**: Pytest report (JSON plugin + JUnit XML for CI); non‑zero exit on failure.
- **Behavior**: Taggable tests (`@pytest.mark.sentinel`), selective runs by domain.

#### Feature: Decision Ledger & Provenance (Python)
- **Description**: Append `DECISIONS.md` entries and emit `ProducedBy=` headers via a Python CLI/MCP.
- **Inputs**: decision metadata (author, scope, rationale).
- **Outputs**: Ledger entry + header snippet for commit messages or file headers.

### Capability: Spec‑Kit Flow Integration
Make Sentinel an invisible augmentation of the standard flow.

#### Feature: `/speckit.constitution` Gate
- **Behavior**: After constitution is generated, run `sentinel contracts validate` and `sentinel context lint` to fail fast when scaffolds drift.

#### Feature: `/speckit.specify` Gate
- **Behavior**: Validate contracts + context; generate Capsules only if green.

#### Feature: `/speckit.plan` & `/speckit.tasks` Gates
- **Behavior**: Preflight validation before plan/task emission; annotate failures with file paths and suggested fixes.

#### Feature: `/speckit.implement` Gate
- **Behavior**: Block merges when sentinel tests or contract validation fail; emit minimal diff hints for agents.

### Capability: MCP Surfaces (Python)
Expose small, deterministic tools for agents without inflating context.

- `mcp.sentinel.contract_validate` → run validator on IDs/paths.
- `mcp.sentinel.sentinel_run` → run only sentinel‑marked tests.
- `mcp.sentinel.decision_log` → append ledger entries and return provenance header text.

### Capability: Bootstrap & CI (Python‑only)
- Single bootstrap command using **uv** (`uv sync`), then `pytest -q` and CLI self‑checks.
- GitHub Actions matrix: Windows, Linux, macOS; uses uv for caching and reproducibility.
</functional-decomposition>

<structural-decomposition>
## Structural Modules (Python‑only)

```
/.taskmaster/docs/sentinel_python_integration_rpg.md   # this PRD
/.tool-versions                                        # python pin only (e.g., 3.12.x)
/.github/workflows/sentinel-ci.yml                     # OS matrix (uv + pytest + CLIs)
/README.md                                             # one‑click Python section
/DECISIONS.md                                          # decision ledger (Python CLI updates)
/sentinelkit/                                          # Python package (the library)
  __init__.py
  contracts/
    __init__.py
    schemas/                                           # YAML/JSON schemas
    fixtures/                                          # sample fixtures for tests
  cli/
    __init__.py
    main.py                                            # `python -m sentinelkit ...`
    contract_validate.py
    context_lint.py
    decision_log.py
    mcp/
      __init__.py
      server.py                                        # JSON‑RPC over stdio
  utils/
    __init__.py
    io.py, errors.py, jsonfmt.py
/tests/
  conftest.py
  sentinels/                                           # pytest suites
  fixtures/                                            # mirrored test data
/pyproject.toml                                        # uv/pep 621; entry points
```

**CLI entry points (pyproject):**
```
[project.scripts]
sentinel = "sentinelkit.cli.main:app"        # Typer‑based root
```

**Commands** (examples):
- `sentinel contracts validate [--id ... | --path ...] [--format json]`
- `sentinel context lint [--capsule <path>]`
- `sentinel sentinels run [--k marker=sentinel]`
- `sentinel decisions append --id D-XXXX --scope path1 path2 --rationale ...`
- MCP server: `python -m sentinelkit.cli.mcp.server`

**Spec‑Kit integration points** (called by Specify CLI and slash commands):
- Post‑init hook for `specify init --sentinel` runs `uv sync && sentinel selfcheck`.
- Slash commands invoke gates via lightweight Python subprocess calls.
</structural-decomposition>

<dependency-graph>
## Dependency Graph (Topological)

1. **Phase 0 — Foundations**
   - P0.1: Confirm Spec‑Kit upstream shape; identify init hook for `--sentinel`.
   - P0.2: Add Python package skeleton (`pyproject.toml`, `sentinelkit/`, `tests/`).
   - P0.3: CI workflow with uv cache and OS matrix.

2. **Phase 1 — Enforcement Primitives (Python)**
   - P1.1: Implement contract validator (schemas + fixtures + CLI + MCP).
   - P1.2: Implement decision ledger appender and provenance header.
   - P1.3: Port sentinel tests to pytest; add `-m sentinel` marker and JSON reporter.

3. **Phase 2 — Spec‑Kit Flow Wiring**
   - P2.1: `specify init --sentinel` bundles Python package stubs + CI + README block; post‑init runs `uv sync`.
   - P2.2: Wire `/speckit.*` commands to call Sentinel gates; ensure helpful failure copy.

4. **Phase 3 — MCP Surfaces**
   - P3.1: JSON‑RPC stdio server exposing contract_validate/sentinel_run/decision_log.
   - P3.2: Smoke tests: initialize → list tools → call → structured pass/fail.

5. **Phase 4 — Removal of Node Enclave**
   - P4.1: Delete `.sentinel/` JS workspace, pnpm configs, and any PowerShell installers.
   - P4.2: Add DECISION entry documenting deprecation and migration.

6. **Phase 5 — Linux Hardening**
   - P5.1: Ensure POSIX paths/shell usage; verify no Windows‑only assumptions.
   - P5.2: Add distro notes (Ubuntu/Fedora) for `uv` install; confirm selfcheck green.
</dependency-graph>

<execution-order>
## Phase Breakdown & Deliverables

### Phase 0 — Foundations
- **Deliverables**: `pyproject.toml`, package skeleton, CI workflow using uv; README “Python‑only” note; `.tool-versions` with Python pin.
- **Exit**: `uv sync` works on Win/Linux/macOS.

### Phase 1 — Enforcement Primitives
- **Deliverables**: `sentinel contracts validate`, `sentinel decisions append`, pytest sentinel suites; MCP stubs.
- **Exit**: Local green suite; JSON outputs stable.

### Phase 2 — Spec‑Kit Flow Wiring
- **Deliverables**: Specify‑CLI `--sentinel` flag integration; post‑init bootstrap; slash‑command gates.
- **Exit**: Fresh scaffold → `uv sync && sentinel selfcheck` → green; `/speckit.*` flows block on failures.

### Phase 3 — MCP Surfaces
- **Deliverables**: MCP server + smoke tests; agent docs for Codex/Cursor.
- **Exit**: Agents can call tools directly; smoke stays green in CI.

### Phase 4 — Remove Node
- **Deliverables**: PR removing `.sentinel/` JS, pnpm files, PowerShell scripts; DECISION entry.
- **Exit**: No Node on path; repo remains green locally and in CI.

### Phase 5 — Linux Hardening
- **Deliverables**: POSIX verification, distro notes, CI Linux badge.
- **Exit**: Identical bootstrap and behavior on Linux/macOS/Windows.
</execution-order>

<risks>
## Technical & Process Risks
- **Spec‑Kit upstream drift**
  - *Mitigation*: Maintain `UPSTREAM.md`; periodic re‑sync task.
- **Validator parity**
  - *Mitigation*: Golden fixtures; JSON output snapshots in tests.
- **Agent UX regressions**
  - *Mitigation*: Gates are additive; emit precise file/line diagnostics; document remediation.
- **Cross‑platform file paths**
  - *Mitigation*: Use `pathlib`, avoid shell‑specific constructs; CI matrix catches drift.
</risks>

<appendix>
## Runbook (local)
```
uv sync
python -m sentinelkit --help
sentinel selfcheck            # runs contract validate + sentinel smoke
pytest -q -m sentinel         # regression suite
```

## Acceptance (what “done” means)
- `specify init --sentinel` produces a repo that, on fresh clone, runs `uv sync && sentinel selfcheck` and passes contracts/context/sentinels/MCP smokes on Windows/Linux/macOS.
- No Node.js, pnpm, or PowerShell anywhere; all CLIs are Python.
- `/speckit.*` commands are transparently gated; failing states block with clear, actionable errors.
- Legacy Node workspace removed; DECISION recorded; CI green.
</appendix>

