#!/usr/bin/env node
/* ProducedBy=BUILDER RulesHash=BUILDER@1.1 Decision=D-0011 */
/**
 * Smoke script for the prompt renderer.
 * Runs router mode then capsule mode for a sample capsule/agent
 * so maintainers can spot regressions quickly.
 *
 * Usage:
 *   pnpm --dir=.sentinel node scripts/orch/prompt-render.smoke.mjs
 *   pnpm --dir=.sentinel node scripts/orch/prompt-render.smoke.mjs ./path/to/capsule.md builder
 */

import path from "node:path";
import { fileURLToPath } from "node:url";
import { renderRouterPrompt, renderCapsulePrompt } from "./prompt-render.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../..");

const DEFAULT_CAPSULE = ".specify/specs/005-capsule-gen/capsule.md";
const DEFAULT_AGENT = "builder";

async function smoke() {
  const capsuleArg = process.argv[2] || DEFAULT_CAPSULE;
  const agentArg = process.argv[3] || DEFAULT_AGENT;
  const capsulePath = path.isAbsolute(capsuleArg) ? capsuleArg : path.resolve(ROOT, capsuleArg);

  console.log(`[smoke] capsule: ${path.relative(ROOT, capsulePath)}`);
  console.log(`[smoke] agent:   ${agentArg}`);

  const routerPrompt = await renderRouterPrompt({ capsulePath, root: ROOT });
  console.log("\n=== Router Prompt Preview (first 400 chars) ===");
  console.log(routerPrompt.slice(0, 400));
  console.log(`\n[smoke] router prompt length: ${routerPrompt.length} chars`);

  const capsulePrompt = await renderCapsulePrompt({
    capsulePath,
    agentId: agentArg,
    root: ROOT
  });
  console.log("\n=== Capsule Prompt Preview (first 400 chars) ===");
  console.log(capsulePrompt.slice(0, 400));
  console.log(`\n[smoke] capsule prompt length: ${capsulePrompt.length} chars`);

  console.log("\n[smoke] prompt-render.smoke complete ✅");
}

smoke().catch((error) => {
  console.error("[smoke] failed:", error?.stack || error);
  process.exit(1);
});
