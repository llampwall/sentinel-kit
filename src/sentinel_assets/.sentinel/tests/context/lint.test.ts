import { describe, it, expect } from "vitest";
import path from "node:path";
import { lintContext } from "../../scripts/context/lint.mts";

const ROOT = path.resolve(__dirname, "..", "..", "..");
const CONFIG = ".sentinel/tests/context/fixtures/context-limits.fixture.json";
const capsule = (name: string) => `.sentinel/tests/context/fixtures/capsules/${name}.md`;

describe("context linter", () => {
  it("passes clean capsules", async () => {
    const summary = await lintContext({
      root: ROOT,
      configPath: CONFIG,
      include: [capsule("valid")]
    });
    expect(summary.issues).toHaveLength(0);
  });

  it("flags missing and forbidden includes", async () => {
    const summary = await lintContext({
      root: ROOT,
      configPath: CONFIG,
      include: [capsule("invalid")]
    });
    const codes = summary.issues.map((issue) => issue.code).sort();
    expect(codes).toContain("MISSING_INCLUDE");
    expect(codes).toContain("FORBIDDEN_INCLUDE");
  });

  it("rejects capsules that exceed line limits", async () => {
    const summary = await lintContext({
      root: ROOT,
      configPath: CONFIG,
      include: [capsule("too-long")]
    });
    expect(summary.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: "MAX_LINES" })
      ])
    );
  });

  it("surfaces warnings when nearing the limit", async () => {
    const summary = await lintContext({
      root: ROOT,
      configPath: CONFIG,
      include: [capsule("warning")]
    });
    expect(summary.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: "NEAR_LIMIT", severity: "warning" })
      ])
    );
    const strictSummary = await lintContext({
      root: ROOT,
      configPath: CONFIG,
      include: [capsule("warning")],
      strict: true
    });
    expect(strictSummary.strict).toBe(true);
    expect(strictSummary.issues).toHaveLength(summary.issues.length);
  });
});
