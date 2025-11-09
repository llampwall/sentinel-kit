import { describe, it, expect } from "vitest";
import path from "node:path";
import os from "node:os";
import { mkdtemp, writeFile } from "node:fs/promises";
import { loadContextLimits } from "../../scripts/context/config.mts";

const ROOT = path.resolve(__dirname, "..", "..", "..");
const FIXTURE_CONFIG = ".sentinel/tests/context/fixtures/context-limits.fixture.json";

describe("context config loader", () => {
  it("loads and normalizes fixture config", async () => {
    const config = await loadContextLimits({ root: ROOT, configPath: FIXTURE_CONFIG });
    expect(config.defaultMaxLines).toBe(8);
    expect(config.warningThreshold).toBeCloseTo(0.75, 2);
    expect(config.forbiddenPaths).toContain(".git");
    expect(config.artifacts[0]?.globs[0]).toBe(".sentinel/tests/context/fixtures/capsules/*.md");
  });

  it("throws on invalid configs", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "context-config-"));
    const badPath = path.join(tempDir, "bad.json");
    await writeFile(
      badPath,
      JSON.stringify({ defaultMaxLines: 5, forbiddenPaths: [] }),
      "utf8"
    );
    await expect(loadContextLimits({ root: ROOT, configPath: badPath })).rejects.toThrow(/schema/i);
  });
});
