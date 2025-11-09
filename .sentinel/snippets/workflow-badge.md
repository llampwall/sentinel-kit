<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0018 -->
### CI & Enforcement

[![Sentinel Kit](https://github.com/github/spec-kit/actions/workflows/sentinel-kit.yml/badge.svg)](https://github.com/github/spec-kit/actions/workflows/sentinel-kit.yml)

The `sentinel-kit` workflow runs on pushes/PRs to `main` and gates the following jobs:
1. **setup-toolchain** – caches Node/pnpm/uv on Ubuntu + Windows.
2. **contracts** – `pnpm --dir=.sentinel validate:contracts`
3. **sentinels** – `pnpm --dir=.sentinel vitest run --config vitest.config.sentinel.ts --reporter=json`
4. **mcp-smoke** – `pnpm --dir=.sentinel mcp:contract-validate:smoke`, `mcp:sentinel-run:smoke`, `mcp:decision-log:smoke`
5. **docs-lint** – `pnpm --dir=.sentinel context:lint`

Failures in any job block merges; artifacts (Vitest JSON, smoke logs) are uploaded for debugging.
