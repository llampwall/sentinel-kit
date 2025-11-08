import { describe, it, expect } from "vitest";
import path from "path";
import os from "os";
import fsp from "fs/promises";
import { validateFixture } from "../../scripts/contracts/validator.mjs";

const ROOT = path.resolve("..");
const VALID_FIXTURE = path.join(
  ROOT,
  ".sentinel",
  "contracts",
  "fixtures",
  "users.v1",
  "get_active.json"
);

async function createTempFixture(contents) {
  const dir = await fsp.mkdtemp(path.join(os.tmpdir(), "sentinel-fixture-"));
  const file = path.join(dir, "fixture.json");
  await fsp.writeFile(file, contents, "utf8");
  return file;
}

describe("contract validator module", () => {
  it("passes a known good fixture", async () => {
    const result = await validateFixture({ contract: "users.v1", fixture: VALID_FIXTURE });
    expect(result.ok).toBe(true);
    expect(result.errors).toEqual([]);
  });

  it("fails when ProducedBy metadata is missing", async () => {
    const invalidPath = await createTempFixture(
      JSON.stringify([
        {
          id: "00000000-0000-4000-8000-000000000010",
          email: "bad@example.com",
          created_at: "2025-01-01T00:00:00Z"
        }
      ])
    );
    await expect(
      validateFixture({ contract: "users.v1", fixture: invalidPath })
    ).rejects.toThrow(/ProducedBy/);
  });

  it("fails schema validation when data breaks the contract", async () => {
    const badData = await createTempFixture(
      JSON.stringify([
        {
          ProducedBy: "FIXTURE RulesHash=FIXTURE@1.0 Decision=D-0001",
          id: "not-a-uuid",
          email: "obviously-bad",
          created_at: "2025-01-01T00:00:00Z"
        }
      ])
    );
    const result = await validateFixture({ contract: "users.v1", fixture: badData });
    expect(result.ok).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });
});
