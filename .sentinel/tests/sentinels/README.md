# Sentinel Tests

Sentinel tests encode previously fixed bugs so regressions are blocked before merge. Use the .sentinel/ Vitest workspace and the helper modules described below.

## Writing a New Sentinel

1. Place tests under .sentinel/tests/sentinels/{area}/sentinel_<slug>.test.ts.
2. Use the fixture helper (Task 3.2) to load data from .sentinel/contracts/fixtures/** and validate against the contract before asserting behavior.
3. Follow Given/When/Then comments and reference the decision ID that introduced the fix (from .sentinel/DECISIONS.md).
4. Commit the new fixture or contract additions alongside the test.

## Commands

```bash
# install tooling (once per repo clone)
make sentinel-install     # macOS/Linux
pwsh ./scripts/setup.ps1  # Windows

# run sentinels
cd .sentinel
pnpm test:sentinels               # full suite
pnpm test:sentinels -- --filter <slug>  # targeted run
pnpm test:sentinels:watch              # watch mode
```

Sentinel CI (Task 10) will run `pnpm test:sentinels -- --filter <slug>` so keep tests deterministic.
