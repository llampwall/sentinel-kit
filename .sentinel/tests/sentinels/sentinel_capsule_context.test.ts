/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0010 */
import { describe, it, expect } from "vitest";
import path from "node:path";
import { buildAllowedContext } from "../../scripts/lib/allowed-context.mjs";

const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");

describe("sentinel: capsule-context helper", () => {
  it("capsule-context includes requested seeds but skips maintainer notes", async () => {
    const allowed = await buildAllowedContext({
      root: REPO_ROOT,
      seeds: [".specify/specs/005-capsule-gen/spec.md", ".sentinel/scripts/md-surgeon.mjs"]
    });

    expect(allowed).toContain(".specify/specs/005-capsule-gen/spec.md");
    expect(allowed).toContain(".sentinel/scripts/md-surgeon.mjs");
    expect(allowed).not.toContain(".sentinel/docs/IMPLEMENTATION.md");
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
