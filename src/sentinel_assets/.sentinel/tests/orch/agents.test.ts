/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0011 */
import { describe, it, expect, afterAll } from "vitest";
import path from "node:path";
import os from "node:os";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { loadAgents } from "../../scripts/orch/agents.mjs";

describe("agent registry helper", () => {
  it("loads built-in agents with role and playbook content", async () => {
    const { agents, lookup } = await loadAgents();
    expect(agents.length).toBeGreaterThan(0);

    const router = lookup.get("router");
    expect(router).toBeTruthy();
    expect(router?.role.content).toMatch(/Mission/i);
    expect(router?.playbook.content).toMatch(/Checklist/i);
  });

  it("throws descriptive errors for misconfigured agents", async () => {
    const tmpRoot = await mkdtemp(path.join(os.tmpdir(), "sentinel-agents-"));
    tempDirs.push(tmpRoot);

    const agentDir = path.join(tmpRoot, ".sentinel", "agents", "broken");
    await mkdir(agentDir, { recursive: true });

    const agentJson = {
      id: "broken",
      name: "Broken Agent",
      rulesHash: "BROKEN@0.0",
      summary: "Intentionally invalid",
      routing_keywords: [],
      mount_paths: [".sentinel/agents/broken/**"],
      prompt_files: [".sentinel/agents/broken/ROLE.md"]
    };
    await writeFile(path.join(agentDir, "agent.json"), JSON.stringify(agentJson, null, 2));
    await writeFile(path.join(agentDir, "ROLE.md"), "# Broken role\n");

    await expect(loadAgents({ root: tmpRoot })).rejects.toThrow(/ROLE\.md and PLAYBOOK\.md/i);
  });
});

const tempDirs: string[] = [];

afterAll(async () => {
  await Promise.all(tempDirs.splice(0).map((dir) => rm(dir, { recursive: true, force: true })));
});
