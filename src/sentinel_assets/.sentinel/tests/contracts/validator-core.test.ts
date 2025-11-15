import { describe, it, expect } from "vitest";
import path from "node:path";
import os from "node:os";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import YAML from "yaml";
import { createContractValidator } from "../../scripts/contracts/validator-core.mjs";

const HEADER = "ProducedBy=TEST RulesHash=TEST@1.0 Decision=D-0001";

async function setupTempContract(): Promise<{
  root: string;
  fixturePath: string;
}> {
  const root = await mkdtemp(path.join(os.tmpdir(), "sentinel-contracts-"));
  const contractsDir = path.join(root, ".sentinel", "contracts");
  const fixturesDir = path.join(contractsDir, "fixtures", "sample.v1");
  await mkdir(fixturesDir, { recursive: true });

  const schemaPath = path.join(contractsDir, "sample.v1.yaml");
  const schema = {
    contract: "sample.v1",
    schema: {
      type: "array",
      items: {
        type: "object",
        required: ["ProducedBy", "value"],
        properties: {
          ProducedBy: { type: "string" },
          value: { type: "number" }
        }
      }
    }
  };
  await writeFile(schemaPath, YAML.stringify(schema), "utf8");

  const fixturePath = path.join(fixturesDir, "ok.json");
  await writeFile(
    fixturePath,
    JSON.stringify([
      {
        ProducedBy: HEADER,
        value: 123
      }
    ]),
    "utf8"
  );

  return { root, fixturePath };
}

describe("validator-core", () => {
  it("validates fixtures using a custom root directory", async () => {
    const { root } = await setupTempContract();
    const validator = createContractValidator({ root });
    const result = await validator.validateAll();
    expect(result.ok).toBe(true);
    expect(result.results).toHaveLength(1);
  });

  it("clears schema cache when requested", async () => {
    const validator = createContractValidator({ root: path.resolve("..") });
    const first = await validator.loadSchemas(true);
    expect(first.size).toBeGreaterThan(0);
    validator.clearCache();
    const second = await validator.loadSchemas();
    expect(second.size).toBeGreaterThan(0);
  });

  it("throws when ProducedBy metadata is missing", () => {
    const validator = createContractValidator({ root: path.resolve("..") });
    expect(() => validator.ensureProducedByHeader({}, "fixture.json")).toThrow(/ProducedBy/);
  });
});
