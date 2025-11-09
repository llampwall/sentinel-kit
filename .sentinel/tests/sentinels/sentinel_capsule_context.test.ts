/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0010 */
import { describe, it, expect } from "vitest";
import path from "node:path";
import { buildAllowedContext } from "../../scripts/lib/allowed-context.mjs";

const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");

describe("sentinel: capsule-context helper", () => {
  it("capsule-context includes .sentinel/context docs plus requested seeds", async () => {
    const allowed = await buildAllowedContext({
      root: REPO_ROOT,
      seeds: [".specify/specs/005-capsule-gen/spec.md", ".sentinel/scripts/md-surgeon.mjs"]
    });

    expect(allowed).toContain(".sentinel/context/IMPLEMENTATION.md");
    expect(allowed).toContain(".specify/specs/005-capsule-gen/spec.md");
    expect(allowed).toContain(".sentinel/scripts/md-surgeon.mjs");
  });

  it("capsule-context rejects missing paths", async () => {
    await expect(
      buildAllowedContext({
        root: REPO_ROOT,
        seeds: ["docs/DOES-NOT-EXIST.md"]
      })
    ).rejects.toThrow(/does not exist/i);
  });
});
