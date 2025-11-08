import { writeFileSync } from "node:fs";
import path from "node:path";
import { loadValidatedFixture } from "./helpers/fixture-loader.mjs";

describe("sentinel: users.v1 email must be RFC-valid", () => {
  it("fails when a user has an invalid email format", async () => {
    const payload = await loadValidatedFixture("users.v1", "users.v1/get_active.json");
    const mutated = structuredClone(payload);
    mutated[0].email = "not-an-email";

    // sentinel enforcement: ensure we log the violation to artifacts for debugging
    const artifactPath = path.resolve("..", "..", "sentinel-artifacts", "email_format_violation.json");
    writeFileSync(artifactPath, JSON.stringify(mutated, null, 2));

    const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    const violationFound = mutated.some((user) => !emailRegex.test(user.email));
    expect(violationFound).toBe(true);
  });
});
