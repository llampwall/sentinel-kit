# Releaser - PLAYBOOK

1) PLAN
   - Define branch and tag strategy (e.g., main -> tags vX.Y.Z).
   - List CI gates: lint, typecheck, unit/integration tests, contract validate, sentinels, build.
   - Choose artifact targets (npm, tarball, container) and environments.

2) WIRE
   - Create or update .github/workflows/*.yml:
     - jobs for lint, typecheck, tests (repo and .sentinel/test), contracts, sentinels, build.
     - cache pnpm/node_modules where safe; set up PNPM store.
     - upload build artifacts for later jobs and release.
   - Add /release/plan.md describing triggers, jobs, gates, and artifacts.

3) PROVE
   - Run workflows on a feature branch; confirm:
     - pnpm -C .sentinel validate:contracts passes.
     - pnpm -C .sentinel test passes (including .sentinel/tests/sentinels/**).
     - repo tests/lint/typecheck/build pass.
   - Fix logs for clarity and flake resistance.

4) VERSION
   - Decide semver bump (patch/minor/major) based on changes and breaking notes.
   - Update version in package.json and/or .sentinel/package.json (or /release/version.txt).
   - Commit with provenance headers; create a signed tag vX.Y.Z.

5) PUBLISH
   - Create a GitHub Release for the tag; attach artifacts.
   - If publishing to a registry, run the appropriate publish step (e.g., npm publish).
   - Generate /release/notes/<version>.md and append /release/CHANGELOG.md.

6) VERIFY
   - Execute post-release smoke under .sentinel/tests/smoke/** (and/or a small CLI canary).
   - Record results and checksums under /release/checksums/<version>.txt if applicable.

7) ANNOUNCE
   - Update the release with links to docs and artifacts.
   - Note Decision-IDs and related capsules in the release body and notes file.

8) ROLLBACK PLAN
   - Document rollback command(s) and criteria in /release/plan.md.
   - If a rollback is executed, tag it and write a brief incident note.

Escalate When:
   - Gates are flaky (loop Verifier/Observer).
   - Credentials/permissions are missing (loop Integrator/Owner).
   - Version skew is detected across multiple packages (loop Builder).
