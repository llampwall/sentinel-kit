<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0018 -->
### CI & Enforcement

[![Sentinel Kit](https://github.com/github/spec-kit/actions/workflows/sentinel-kit.yml/badge.svg)](https://github.com/github/spec-kit/actions/workflows/sentinel-kit.yml)

The `sentinel-kit` workflow runs on pushes/PRs to `main` and gates the following jobs:
1. **setup-toolchain** – caches uv and installs the shared Python workspace.
2. **contracts** – `uv run sentinel contracts validate`
3. **sentinels** – `uv run sentinel sentinels run --json-report test-results/sentinels.json --junit test-results/sentinels.xml`
4. **mcp-smoke** – `uvx sentinel mcp smoke`
5. **docs-lint** – `uv run sentinel context lint --strict`

Failures in any job block merges; artifacts (JSON/junit reports, smoke logs) are uploaded for debugging.
