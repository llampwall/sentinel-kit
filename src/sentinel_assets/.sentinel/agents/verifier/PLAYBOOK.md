# Verifier - PLAYBOOK

1) DISCOVER
   - Read capsule Goal and Acceptance.
   - Identify modules, flows, and contracts that must be exercised.

2) REPRODUCE
   - Write a minimal failing test or MRE.
   - If a contract is involved, add good/bad fixtures that demonstrate the issue.

3) SPECIFY
   - Create /verification/<capsule>/plan.md with:
     - Scope under test
     - Commands to run locally
     - Assertions that prove success
     - Any contract or sentinel hooks to run

4) IMPLEMENT
   - Add tests under /src/**/__tests__/** or /tests/** or /.sentinel/tests/**.
   - Add fixtures under /.sentinel/contracts/fixtures/** if schema-driven.
   - Add or update sentinels under /.sentinel/sentinels/** for critical paths.
   - Provide mocks and test-only helpers as needed (no production edits).

5) VERIFY
   - Run unit/integration suites (e.g., `pnpm test`).
   - Run contract checks if present (e.g., `pnpm -C .sentinel validate:contracts`).
   - Run sentinel or smoke scripts (e.g., `pnpm -C .sentinel test:sentinels`).
   - Ensure failures are actionable and reproducible; resolve flake.

6) PACKAGE
   - Update plan.md with final commands and results summary.
   - Ensure provenance headers (Decision-ID, Produced-By, Related-Capsule) are present.
   - Keep diffs minimal and test-focused.

7) HANDOFF
   - If tests expose required production changes, tag Builder or Refactorer.
   - If CI gates are missing, tag Releaser to wire them.
