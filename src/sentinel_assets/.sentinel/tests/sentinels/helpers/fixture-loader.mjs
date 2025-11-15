import path from "path";
import { fileURLToPath } from "url";
import { readFile } from "node:fs/promises";
import { validateFixture } from "../../../scripts/contracts/validator.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../../..");
const FIXTURE_ROOT = path.join(ROOT, ".sentinel", "contracts", "fixtures");

/**
 * Load and validate a fixture before running sentinel assertions.
 * @param {string} contract - Contract name (e.g., "users.v1")
 * @param {string} fixtureRelativePath - Path inside .sentinel/contracts/fixtures
 */
export async function loadValidatedFixture(contract, fixtureRelativePath) {
  const target = path.join(FIXTURE_ROOT, fixtureRelativePath);
  const result = await validateFixture({ contract, fixture: target });
  if (!result.ok) {
    const errors = (result.errors || []).map((err) => err.message || JSON.stringify(err)).join(" | ");
    throw new Error('Fixture validation failed for ' + fixtureRelativePath + ': ' + errors);
  }
  if (result.data) return result.data;
  const raw = await readFile(target, "utf8");
  return JSON.parse(raw);
}
