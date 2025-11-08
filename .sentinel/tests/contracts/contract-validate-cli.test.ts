import { describe, it, expect } from "vitest";
import path from "path";
import os from "os";
import fsp from "fs/promises";
import { spawn } from "node:child_process";

const CLI = path.resolve("scripts", "contract-validate.mjs");
const ROOT = path.resolve("..");

function runCli(args) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [CLI, ...args], {
      cwd: path.join(ROOT, ".sentinel"),
      stdio: ["ignore", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => (stdout += chunk.toString()));
    child.stderr.on("data", (chunk) => (stderr += chunk.toString()));
    child.on("close", (code) => resolve({ code, stdout, stderr }));
  });
}

async function createInvalidFixture() {
  const dir = await fsp.mkdtemp(path.join(os.tmpdir(), "sentinel-cli-"));
  const file = path.join(dir, "invalid.json");
  await fsp.writeFile(
    file,
    JSON.stringify([
      {
        id: "not-a-uuid",
        email: "missing-at-sign",
        created_at: "2025-01-01T00:00:00Z"
      }
    ]),
    "utf8"
  );
  return file;

}

describe("contract-validate CLI", () => {
  it("returns ok JSON for valid contract", async () => {
    const result = await runCli(["--contract", "users.v1"]);
    expect(result.code).toBe(0);
    const parsed = JSON.parse(result.stdout);
    expect(parsed.ok).toBe(true);
    expect(Array.isArray(parsed.results)).toBe(true);
  });

  it("fails when schema validation errors occur", async () => {
    const invalidFixture = await createInvalidFixture();
    const result = await runCli(["--contract", "users.v1", "--fixture", invalidFixture]);
    expect(result.code).toBe(1);
    const parsed = JSON.parse(result.stdout);
    expect(parsed.ok).toBe(false);
  });
});
