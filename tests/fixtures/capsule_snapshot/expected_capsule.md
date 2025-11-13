<!--
  Capsule Template
  ----------------
  - The capsule generator consumes this file by replacing the token placeholders below.
  - Keep instruction comments inside HTML comments so generated capsules stay clean.
  - Manual authors can duplicate this file, fill in the tokens, and remove any unused comments.
  - Tokens available:
      PRODUCED_BY (full provenance header)
      CAPSULE_ID  (slug@hash)
      GOAL
      REQUIRED_OUTPUTS
      ACCEPTANCE_CRITERIA
      ALLOWED_CONTEXT
      ROUTER_NOTES
-->
<!--
  ProducedBy=ROUTER
  RulesHash=ROUTER@1.0
  Decision=D-TEST
-->

# Capsule spec@89ff708e

## Goal
Produce a deterministic capsule for regression testing so future refactors can compare output byte-for-byte.

## Required Outputs
- Capsule file updated with ProducedBy header, Allowed Context, and router notes.
- README snippet referencing the CLI workflow.

## Acceptance Criteria
- Capsule hashes include the slug plus content digest.
- Allowed Context matches the seeds defined in the plan.

## Allowed Context
- .sentinel/context/fixtures/capsules/duplicate.md
- .sentinel/context/fixtures/capsules/escape.md
- .sentinel/context/fixtures/capsules/forbidden.md
- .sentinel/context/fixtures/capsules/line-299.md
- .sentinel/context/fixtures/capsules/line-300.md
- .sentinel/context/fixtures/capsules/line-301.md
- .sentinel/context/fixtures/capsules/missing-context.md
- .sentinel/context/fixtures/capsules/missing-include.md
- .sentinel/context/fixtures/context-limits.fixture.json
- README.md
- tests/fixtures/capsule_snapshot/spec/plan.md
- tests/fixtures/capsule_snapshot/spec/spec.md
- tests/fixtures/capsule_snapshot/spec/tasks.md

## Router Notes
- ROUTER assigns Builder by default.
- Keep Allowed Context restricted to README + spec docs.
