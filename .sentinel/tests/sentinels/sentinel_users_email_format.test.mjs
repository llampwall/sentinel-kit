/* ProducedBy=SCRIBE RulesHash=DOCS@1.0 Decision=D-0003 */
/**
 * Sentinel test for the users_consumer module.
 * Guards against regressions where invalid email formats pass contract validation.
 */
import { describe, it, expect } from "vitest";
import { loadValidatedFixture } from "./helpers/fixture-loader.mjs";

const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

describe("sentinel: users.v1 email must be RFC-valid", () => {
  it("guards regression D-0001: invalid emails slip past validator", async () => {
    // DecisionRef: D-0001 (Email format enforcement)
    // Given a validated users.v1 fixture
    const payload = await loadValidatedFixture("users.v1", "users.v1/get_active.json");

    // When we scan every email for RFC compliance
    const invalidRecord = payload.find((record) => !EMAIL_REGEX.test(record.email));

    // Then nothing should violate the pattern; failure indicates regression
    expect(invalidRecord).toBeUndefined();
  });
});
