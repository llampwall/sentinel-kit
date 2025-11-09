import { describe, it, expect, beforeEach, afterEach } from "vitest";
import path from "node:path";
import os from "node:os";
import fsp from "node:fs/promises";
import { spawnSync } from "node:child_process";

const CLI = path.resolve("scripts", "decision-log.mjs");

async function createTempLedger(nextId = "D-0005") {
  const dir = await fsp.mkdtemp(path.join(os.tmpdir(), "decision-ledger-"));
  const ledger = path.join(dir, "DECISIONS.md");
  const template = `<!-- header -->\n\n# Decisions Ledger\n\n## NEXT_ID\n${nextId}\n\n## Format\n\nID: D-0001\nDate: 2025-11-01\nAuthor: Seed\nScope: init\nDecision: seed entry\nRationale: placeholder\nOutputs: none\nSupersedes: none\n`;
  await fsp.writeFile(ledger, template, "utf8");
  return { dir, ledger };
}

function runCli(args) {
  return spawnSync(process.execPath, [CLI, ...args], {
    cwd: path.resolve("."),
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"]
  });
}

describe("decision-log CLI", () => {
  const tempDirs = [];

  afterEach(async () => {
    for (const dir of tempDirs.splice(0)) {
      await fsp.rm(dir, { recursive: true, force: true });
    }
  });

  it("appends a decision and increments NEXT_ID", async () => {
    const { dir, ledger } = await createTempLedger("D-0005");
    tempDirs.push(dir);

    const result = runCli([
      "--ledger",
      ledger,
      "--author",
      "Builder",
      "--scope",
      ".sentinel/scripts",
      "--summary",
      "Add decision log CLI",
      "--rationale",
      "Automate provenance entries",
      "--outputs",
      ".sentinel/scripts/decision-log.mjs"
    ]);

    expect(result.status).toBe(0);
    const payload = JSON.parse(result.stdout.trim());
    expect(payload.id).toBe("D-0005");
    expect(payload.snippets.plain).toMatch(/ProducedBy=BUILDER/);

    const updated = await fsp.readFile(ledger, "utf8");
    expect(updated).toMatch(/## NEXT_ID\s*D-0006/);
    expect(updated).toMatch(/ID: D-0005/);
  });

  it("fails when required args are missing", async () => {
    const { dir, ledger } = await createTempLedger();
    tempDirs.push(dir);

    const result = runCli(["--ledger", ledger]);
    expect(result.status).toBe(1);
    expect(result.stderr || result.stdout).toMatch(/Missing required option/);
  });

  it("errors when ledger is locked", async () => {
    const { dir, ledger } = await createTempLedger();
    tempDirs.push(dir);
    const lockPath = `${ledger}.lock`;
    await fsp.writeFile(lockPath, "locked", "utf8");

    const result = runCli([
      "--ledger",
      ledger,
      "--author",
      "Builder",
      "--scope",
      ".sentinel/scripts",
      "--summary",
      "Test lock",
      "--rationale",
      "Ensure lock handling",
      "--outputs",
      "README.md"
    ]);

    expect(result.status).toBe(1);
    expect(result.stderr || result.stdout).toMatch(/locked/);
  });
});
