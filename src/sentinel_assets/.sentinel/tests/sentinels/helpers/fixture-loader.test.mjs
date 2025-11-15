import { describe, it, expect, afterAll } from "vitest";
import path from "path";
import { mkdir, writeFile, rm } from "node:fs/promises";
import { fileURLToPath } from "url";
import { loadValidatedFixture } from "./fixture-loader.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FIXTURE_DIR = path.resolve(__dirname, "../../../contracts/fixtures");
const TEMP_RELATIVE = "users.v1/__invalid_test_fixture.json";
const TEMP_ABS = path.join(FIXTURE_DIR, TEMP_RELATIVE);

async function ensureTempFixture() {
  await mkdir(path.dirname(TEMP_ABS), { recursive: true });
  await writeFile(
    TEMP_ABS,
    JSON.stringify([
      {
        id: "00000000-0000-4000-8000-000000000099",
        email: "missing-header@example.com",
        created_at: "2025-01-01T00:00:00Z"
      }
    ])
  );
}

afterAll(async () => {
  await rm(TEMP_ABS, { force: true });
});

describe("fixture-loader", () => {
  it("returns parsed data for a known good fixture", async () => {
    const payload = await loadValidatedFixture("users.v1", "users.v1/get_active.json");
    expect(Array.isArray(payload)).toBe(true);
    expect(payload.length).toBeGreaterThan(0);
  });

  it("throws when the ProducedBy header is missing", async () => {
    await ensureTempFixture();
    await expect(loadValidatedFixture("users.v1", TEMP_RELATIVE)).rejects.toThrow(/ProducedBy header/);
  });
});
