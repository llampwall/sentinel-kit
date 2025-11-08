/* ProducedBy=SCRIBE RulesHash=DOCS@1.0 Decision=D-0003 */
/**
 * Sentinel test for the users_consumer module.
 * Guards against regressions where invalid email formats pass contract validation.
 */
import { describe, it, expect } from "vitest";
import { loadActiveUsers, validateUsers } from "../../src/users_consumer.mjs";

describe("sentinel: users.v1 email must be RFC-valid", () => {
  it("fails when a user has an invalid email format", async () => {
    const data = await loadActiveUsers();
    const broken = structuredClone ? structuredClone(data) : JSON.parse(JSON.stringify(data));
    broken[0].email = "not-an-email";
    const { ok } = await validateUsers(broken);
    expect(ok).toBe(false);
  });
});
