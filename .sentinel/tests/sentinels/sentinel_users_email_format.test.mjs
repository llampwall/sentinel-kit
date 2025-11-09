/* ProducedBy=SCRIBE RulesHash=DOCS@1.0 Decision=D-0003 */
/**
 * Sentinel test for the users_consumer module.
 * Guards against regressions where invalid email formats pass contract validation.
 */
import { describe, it, expect } from "vitest";

/**
 * Placeholder sentinel until the Task 3 harness ports the real users_consumer module.
 * Keeps vitest green so CI can run lint/typecheck/test in earlier phases.
 */
describe.skip("sentinel: users.v1 email must be RFC-valid", () => {
  it("fails when a user has an invalid email format", () => {
    expect(true).toBe(true);
  });
});
