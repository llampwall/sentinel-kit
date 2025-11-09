/* ProducedBy=BUILDER RulesHash=BUILDER@1.1 Decision=D-0011 */
import { describe, it, expect, afterAll } from "vitest";
import path from "node:path";
import { readFile, rm, writeFile, mkdtemp } from "node:fs/promises";
import os from "node:os";
import { spawnSync } from "node:child_process";
import {
  parseArgs,
  renderRouterPrompt,
  renderCapsulePrompt,
  validateRouterPayload,
  writeRouterLog
} from "../../scripts/orch/prompt-render.mjs";

const ROOT = path.resolve("..");
const CAPSULE = ".specify/specs/005-capsule-gen/capsule.md";
const cleanupPaths: string[] = [];
const cleanupDirs: string[] = [];
const CLI_SCRIPT = path.join(".sentinel", "scripts", "orch", "prompt-render.mjs");

describe("prompt-render CLI", () => {
  it("parses required flags", () => {
    expect(
      parseArgs(["--mode", "router", "--capsule", CAPSULE, "--output", "out.md"])
    ).toEqual({
      mode: "router",
      capsule: CAPSULE,
      agent: undefined,
      output: "out.md"
    });
    expect(() => parseArgs(["--mode", "router"])).toThrow(/--capsule/);
    expect(() => parseArgs(["--capsule", CAPSULE])).toThrow(/--mode/);
    expect(() =>
      parseArgs(["--mode", "capsule", "--capsule", CAPSULE])
    ).toThrow(/--agent/);
  });

  it("renders router prompt with agent roster", async () => {
    const prompt = await renderRouterPrompt({ capsulePath: CAPSULE, root: ROOT });
    expect(prompt).toMatch(/Path:\s+\.specify\/specs\/005-capsule-gen\/capsule\.md/i);
    expect(prompt).toMatch(/Available Agents/i);
    expect(prompt).toMatch(/Router · Role/i);
  });

  it("renders capsule prompt for builder agent", async () => {
    const prompt = await renderCapsulePrompt({
      capsulePath: CAPSULE,
      agentId: "builder",
      root: ROOT
    });
    expect(prompt).toMatch(/You are \*\*Builder\*\*/);
    expect(prompt).toMatch(/Allowed Context/i);
    expect(prompt).toMatch(/Path:\s+\.specify\/specs\/005-capsule-gen\/capsule\.md/i);
  });

  it("validates router payloads and throws on errors", () => {
    expect(() =>
      validateRouterPayload({
        leadAgent: "builder",
        requiredOutputs: ["README.md"],
        contextToMount: [".specify/specs/005-capsule-gen/capsule.md"]
      })
    ).not.toThrow();

    expect(() =>
      validateRouterPayload({
        leadAgent: "builder",
        requiredOutputs: [],
        contextToMount: [".specify/specs/005-capsule-gen/capsule.md"]
      })
    ).toThrow(/requiredOutputs/i);
  });

  it("writes router logs with hashed capsule path", async () => {
    const logPath = await writeRouterLog({
      capsulePath: CAPSULE,
      payload: {
        leadAgent: "builder",
        requiredOutputs: ["README.md"],
        acceptanceCriteria: ["README updated"],
        contextToMount: [CAPSULE],
        notes: "test entry"
      },
      root: ROOT
    });
    cleanupPaths.push(logPath);
    const raw = await readFile(logPath, "utf8");
    const record = JSON.parse(raw.trim());
    expect(record.capsule).toMatch(/\.specify\/specs\/005-capsule-gen\/capsule\.md/);
    expect(record.payload.leadAgent).toBe("builder");
    expect(record.capsuleHash).toMatch(/^[0-9a-f]{8}$/i);
  });
});

describe("prompt-render CLI integration", () => {
  it("emits router prompt via CLI", () => {
    const result = spawnSync(process.execPath, [CLI_SCRIPT, "--mode", "router", "--capsule", CAPSULE], {
      cwd: ROOT,
      encoding: "utf8"
    });
    expect(result.status).toBe(0);
    expect(result.stdout).toMatch(/Available Agents/i);
  });

  it("emits capsule prompt via CLI", () => {
    const result = spawnSync(process.execPath, [CLI_SCRIPT, "--mode", "capsule", "--capsule", CAPSULE, "--agent", "builder"], {
      cwd: ROOT,
      encoding: "utf8"
    });
    expect(result.status).toBe(0);
    expect(result.stdout).toMatch(/You are \*\*Builder\*\*/);
  });

  it("validates router JSON and writes log when --router-json provided", async () => {
    const tmpDir = await mkdtemp(path.join(os.tmpdir(), "prompt-render-cli-"));
    cleanupDirs.push(tmpDir);
    const jsonPath = path.join(tmpDir, "router.json");
    await writeFile(
      jsonPath,
      JSON.stringify({
        leadAgent: "builder",
        requiredOutputs: ["README.md"],
        acceptanceCriteria: ["README updated"],
        contextToMount: [CAPSULE],
        notes: "CLI test"
      }),
      "utf8"
    );
    const result = spawnSync(
      process.execPath,
      [
        CLI_SCRIPT,
        "--mode",
        "router",
        "--capsule",
        CAPSULE,
        "--router-json",
        jsonPath
      ],
      {
        cwd: ROOT,
        encoding: "utf8"
      }
    );
    expect(result.status).toBe(0);
    expect(result.stderr).toMatch(/router log ->/i);
  });
});

afterAll(async () => {
  await Promise.all(
    cleanupPaths.splice(0).map((file) => rm(file, { force: true }))
  );
  await Promise.all(
    cleanupDirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true }))
  );
});
