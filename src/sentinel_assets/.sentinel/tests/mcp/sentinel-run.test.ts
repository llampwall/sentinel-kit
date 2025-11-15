import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

const mockExecutor = vi.fn();

describe("sentinel-run MCP tool", () => {
  beforeEach(() => {
    mockExecutor.mockReset();
  });

  afterEach(async () => {
    const module = await import("../../scripts/mcp/sentinel-run.mjs");
    module.__resetSentinelExecutor();
  });

  it("runs sentinel tests and returns summary", async () => {
    const summary = { success: true, stats: { tests: 1, failures: 0 } };
    mockExecutor.mockResolvedValue({
      code: 0,
      stdout: JSON.stringify(summary),
      stderr: "",
      summary
    });
    const module = await import("../../scripts/mcp/sentinel-run.mjs");
    module.__setSentinelExecutor(mockExecutor);
    const result = await module.runSentinelTool({ filter: "capsule" });
    expect(mockExecutor).toHaveBeenCalledWith({ filter: "capsule" });
    expect(result.ok).toBe(true);
    expect(result.content[0].json.summary).toEqual(summary);
  });

  it("marks response as error when exit code non-zero", async () => {
    const summary = { success: false };
    mockExecutor.mockResolvedValue({
      code: 1,
      stdout: JSON.stringify(summary),
      stderr: "boom",
      summary
    });
    const module = await import("../../scripts/mcp/sentinel-run.mjs");
    module.__setSentinelExecutor(mockExecutor);
    const result = await module.runSentinelTool({});
    expect(result.ok).toBe(false);
    expect(result.content[0].json.exitCode).toBe(1);
  });
});
