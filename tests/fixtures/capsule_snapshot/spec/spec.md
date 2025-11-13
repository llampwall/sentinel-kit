# Golden Feature Capsule

## Goal
Produce a deterministic capsule for regression testing so future refactors can compare output byte-for-byte.

## Background
- This fixture mirrors a minimal Spec-Kit feature with plan/tasks files.
- The generator should derive Allowed Context from the spec seeds plus `.sentinel/context/**`.
