/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0010 */
import { describe, it, expect, afterEach } from "vitest";
import path from "node:path";
import { mkdtemp, rm, readFile, writeFile } from "node:fs/promises";
import { generateCapsule } from "../scripts/capsule-create.mjs";

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const SPEC_DIR = path.resolve(REPO_ROOT, ".specify/specs/005-capsule-gen");

const tempDirs: string[] = [];

afterEach(async () => {
  while (tempDirs.length) {
    const dir = tempDirs.pop();
    if (dir) {
      await rm(dir, { recursive: true, force: true });
    }
  }
});

async function cloneSpecDir(): Promise<string> {
  const dir = await mkdtemp(path.join(REPO_ROOT, ".specify", "specs", "tmp-capsule-"));
  tempDirs.push(dir);
  const files = ["spec.md", "plan.md", "tasks.md"];
  await Promise.all(
    files.map(async (file) => {
      const src = await readFile(path.join(SPEC_DIR, file), "utf8");
      await writeFile(path.join(dir, file), src, "utf8");
    })
  );
  return dir;
}

describe("capsule-create", () => {
  it("renders deterministic capsule content for Task 5 spec", async () => {
    const { capsuleId, content } = await generateCapsule({
      specDir: SPEC_DIR,
      decision: "D-TEST",
      agent: "ROUTER",
      rulesHash: "ROUTER@Test",
      write: false,
      root: REPO_ROOT
    });

    expect(capsuleId).toMatch(/^005-capsule-gen@/);
    expect(content).toMatchSnapshot();
  });

  it("writes capsule.md to the spec directory", async () => {
    const copyDir = await cloneSpecDir();
    const { outPath } = await generateCapsule({
      specDir: copyDir,
      decision: "D-FAKE",
      agent: "ROUTER",
      root: REPO_ROOT
    });

    expect(outPath.endsWith("capsule.md")).toBe(true);
    const rendered = await readFile(outPath, "utf8");
    expect(rendered).toContain("## Goal");
    expect(rendered).toContain("## Allowed Context");
  });
});
