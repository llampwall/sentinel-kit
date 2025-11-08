import path from "path";
import { fileURLToPath } from "url";
import { validateFixture } from "../../../scripts/contracts/validator.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../../..");

/**
 * Load and validate a fixture before running sentinel assertions.
 * @param {string} contract - Contract name (e.g., "users.v1")
 * @param {string} fixtureRelativePath - Relative path inside `.sentinel/contracts/fixtures`
 */
export async function loadValidatedFixture(contract, fixtureRelativePath) {
  const fixture = path.join(ROOT, ".sentinel", "contracts", "fixtures", fixtureRelativePath);
  const result = await validateFixture({ contract, fixture });
  if (!result.ok) {
    const errors = result.errors?.map((e) => e.message ?? JSON.stringify(e)).join(" | ");
    throw new Error(`Fixture validation failed for ${fixture}: ${errors}`);
  }
  return result.data ?? (await import("node:fs/promises")).readFile(fixture, "utf8").then(JSON.parse);
}
