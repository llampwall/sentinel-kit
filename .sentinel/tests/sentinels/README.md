# Sentinel Tests

Sentinel tests codify previously fixed bugs so regressions are caught before merge. They run from the .sentinel workspace using the Vitest config introduced in Task 3.1.

## Writing a New Sentinel

1. Place tests under .sentinel/tests/sentinels/[area]/sentinel_[slug].test.ts.
2. Use the fixture helper (./helpers/fixture-loader.mjs) to load data from .sentinel/contracts/fixtures/** and validate contracts before asserting behavior.
3. Annotate each test with a DecisionRef: D-XXXX comment and outline Given/When/Then steps so the regression context stays clear.
4. Stamp the ProducedBy= header (from the decision-log CLI) on every new or modified file.
5. Commit any fixture or contract edits alongside the sentinel.

## Commands

    # install tooling (once per repo clone)
    make sentinel-install     # macOS/Linux
    pwsh ./scripts/setup.ps1  # Windows

    # run sentinels
    cd .sentinel
    pnpm test:sentinels                     # full suite
    pnpm test:sentinels -- --filter [slug]  # targeted run
    pnpm test:sentinels:watch               # watch mode

## CI Expectations

CI should run pnpm test:sentinels --runInBand to avoid flake. Keep tests deterministic (no timers, random data, or network calls) and prefer pure assertions over filesystem writes unless a capsule explicitly requires artifacts.