#!/usr/bin/env node
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0004 */
/**
 * Prompt Renderer (minimal, single script entry point)
 * - Discovers agents dynamically by listing .sentinel/agents/<agent>/ROLE.md
 * - Renders Router prompt (injects AVAILABLE_AGENTS_JSON + ROUTING_HINTS_JSON + capsule)
 * - Renders Lead Agent prompt (injects MOUNTED_AGENT_PATH + AGENT tokens + capsule)
 *
 * TODO: collapse router + agent modes into a single flow once the CLI can capture
 *       and reuse the router's JSON automatically.
 *
 * Usage:
 *   node scripts/orch/prompt-render.mjs --capsule <path> --mode router
 *   node scripts/orch/prompt-render.mjs --capsule <path> --mode capsule --agent <AgentId>
 *
 * No external deps; Node stdlib only.
 */

import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../..");

function arg(flag, fallback = undefined) {
  const i = process.argv.indexOf(flag);
  if (i === -1) return fallback;
  return process.argv[i + 1] && !process.argv[i + 1].startsWith("--")
    ? process.argv[i + 1]
    : true;
}

function die(msg, code = 1) {
  console.error(msg);
  process.exit(code);
}

async function readText(p) {
  return fs.readFile(path.resolve(ROOT, p), "utf8");
}

function replaceAll(s, map) {
  let out = s;
  for (const [k, v] of Object.entries(map)) {
    const token = new RegExp(escapeRegExp(k), "g");
    out = out.replace(token, v);
  }
  return out;
}
function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function discoverAgents() {
  const agentsDir = path.resolve(ROOT, ".sentinel", "agents");
  let dirents = [];
  try {
    dirents = await fs.readdir(agentsDir, { withFileTypes: true });
  } catch {
    return { available: [], hints: [], mounts: new Map(), lookup: new Map() };
  }

  const records = [];
  for (const entry of dirents) {
    if (!entry.isDirectory()) continue;
    const id = entry.name;
    const rolePathAbs = path.join(agentsDir, id, "ROLE.md");
    try {
      await fs.access(rolePathAbs);
    } catch {
      continue;
    }
    records.push({
      id,
      rolePath: normalizeForPrompt(path.relative(ROOT, rolePathAbs)),
      mount: `.sentinel/agents/${id}/**`
    });
  }

  records.sort((a, b) => a.id.localeCompare(b.id, undefined, { sensitivity: "base" }));
  const available = records.map((r) => r.id);
  const hints = records.map((r) => ({ id: r.id, role: r.rolePath }));
  const mounts = new Map(records.map((r) => [r.id, r.mount]));
  const lookup = new Map(records.map((r) => [r.id.toLowerCase(), r.id]));

  return { available, hints, mounts, lookup };
}

function normalizeForPrompt(p) {
  return p.split(path.sep).join("/");
}

async function renderRouter({ capsulePath }) {
  const tpl = await readText(".sentinel/prompts/sentinel.router.md");
  const cap = await readText(capsulePath);
  const { available, hints } = await discoverAgents();

  if (!available.length) die("No agents discovered in .sentinel/agents/*");

  const out = replaceAll(tpl, {
    "{{AVAILABLE_AGENTS_JSON}}": JSON.stringify(available),
    "{{ROUTING_HINTS_JSON}}": JSON.stringify(hints, null, 2),
    "{{CAPSULE_PATH}}": capsulePath,
    "{{CAPSULE_CONTENT}}": cap
  });
  process.stdout.write(out);
}

async function renderCapsule({ capsulePath, agent }) {
  if (!agent) die("--agent is required for --mode capsule");
  const tpl = await readText(".sentinel/prompts/sentinel.capsule.md");
  const cap = await readText(capsulePath);
  const { available, mounts, lookup } = await discoverAgents();
  const canonical = lookup.get(agent.toLowerCase());
  if (!canonical) {
    die(`Agent '${agent}' not found. Available: ${available.join(", ")}`);
  }

  const mounted = mounts.get(canonical) || `.sentinel/agents/${canonical}/**`;

  const out = replaceAll(tpl, {
    "{{AGENT}}": canonical,
    "{{AGENT_UPPER}}": canonical.toUpperCase(),
    "{{AGENT_LOWER}}": canonical.toLowerCase(),
    "{{MOUNTED_AGENT_PATH}}": mounted,
    "{{CAPSULE_PATH}}": capsulePath,
    "{{CAPSULE_CONTENT}}": cap
  });
  process.stdout.write(out);
}

async function main() {
  const mode = arg("--mode");
  const capsulePath = arg("--capsule");
  const agent = arg("--agent");

  if (!mode || !capsulePath) {
    die(
      [
        "Usage:",
        "  node scripts/orch/prompt-render.mjs --capsule <path> --mode router",
        "  node scripts/orch/prompt-render.mjs --capsule <path> --mode capsule --agent <AgentId>"
      ].join("\n")
    );
  }

  if (mode === "router") return renderRouter({ capsulePath });
  if (mode === "capsule") return renderCapsule({ capsulePath, agent });
  die(`Unknown --mode '${mode}' (expected 'router' or 'capsule')`);
}

main().catch((e) => {
  console.error(e?.stack || String(e));
  process.exit(1);
});
