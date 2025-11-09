#!/usr/bin/env node
// @ts-check
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0010 */
/**
 * Capsule generator CLI.
 * Reads a Spec-Kit feature directory (spec/plan/tasks), builds a deterministic capsule.md,
 * enforces the <=300 line budget, and validates Allowed Context entries.
 *
 * Usage:
 *   pnpm -C .sentinel capsule:create --spec ../.specify/specs/005-capsule-gen --decision D-0010
 */

import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import crypto from "node:crypto";
import process from "node:process";
import { buildAllowedContext } from "./lib/allowed-context.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");
const TEMPLATE_PATH = path.resolve(__dirname, "../templates/capsule.md");
const MAX_LINES = 300;

/**
 * @param {string} msg
 * @returns {never}
 */
const die = (msg) => {
  console.error(msg);
  process.exit(1);
};

/**
 * @param {string} flag
 * @param {string | undefined} [fallback]
 * @returns {string | true | undefined}
 */
const arg = (flag, fallback = undefined) => {
  const idx = process.argv.indexOf(flag);
  if (idx === -1) return fallback;
  const next = process.argv[idx + 1];
  if (!next || next.startsWith("--")) return true;
  return next;
};

/**
 * @param {string} flag
 */
const hasFlag = (flag) => process.argv.includes(flag);

/**
 * @param {string} s
 */
const escapeRegex = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/**
 * Extract a markdown section by heading text (case-insensitive).
 * @param {string} markdown
 * @param {string} heading
 */
export function extractSection(markdown, heading) {
  const lines = markdown.split(/\r?\n/);
  const matcher = new RegExp(`^(#{1,6})\\s+${escapeRegex(heading)}\\s*$`, "i");
  let capturing = false;
  let depth = 0;
  const bucket = [];

  for (const line of lines) {
    const headerMatch = line.match(/^(#{1,6})\s+(.*?)\s*$/);
    if (headerMatch) {
      if (matcher.test(line)) {
        capturing = true;
        depth = headerMatch[1].length;
        continue;
      }
      if (capturing && headerMatch[1].length <= depth) break;
    }
    if (capturing) bucket.push(line);
  }

  return bucket.join("\n").trim();
}

/**
 * Parse a bullet/ordered list section into items.
 * @param {string} section
 * @returns {string[]}
 */
export function extractList(section) {
  const lines = section.split(/\r?\n/);
  /** @type {string[]} */
  const items = [];
  let current = "";
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const bullet = line.match(/^([-*]|\d+\.)\s+(.*)$/);
    if (bullet) {
      if (current) items.push(current);
      current = bullet[2].trim();
    } else if (current) {
      current = `${current} ${line}`;
    } else {
      current = line;
    }
  }
  if (current) items.push(current);
  return items;
}

/**
 * @param {string} text
 */
const formatParagraph = (text) =>
  text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .join("\n");

/**
 * @param {string[]} items
 */
const formatList = (items) => items.map((item) => `- ${item}`).join("\n");

/**
 * @param {{agent: string; rulesHash: string; decision: string}} params
 */
const renderHeader = ({ agent, rulesHash, decision }) =>
  `<!-- ProducedBy=${agent} RulesHash=${rulesHash} Decision=${decision} -->`;

/**
 * @param {string} slug
 * @param {string} payload
 */
function hashCapsuleId(slug, payload) {
  const hash = crypto.createHash("sha256").update(slug).update(payload).digest("hex");
  return `${slug}@${hash.slice(0, 8)}`;
}

/**
 * @typedef {Object} CapsuleTokens
 * @property {string} PRODUCED_BY
 * @property {string} CAPSULE_ID
 * @property {string} GOAL
 * @property {string} REQUIRED_OUTPUTS
 * @property {string} ACCEPTANCE_CRITERIA
 * @property {string} ALLOWED_CONTEXT
 * @property {string} ROUTER_NOTES
 */

/**
 * @param {CapsuleTokens} tokens
 */
async function renderCapsule(tokens) {
  const rawTemplate = await readFile(TEMPLATE_PATH, "utf8");
  const template = rawTemplate.replace(/^\s*<!--[\s\S]*?-->\s*/u, "");
  let content = template;
  for (const [key, value] of Object.entries(tokens)) {
    const token = new RegExp(`{{${key}}}`, "g");
    content = content.replace(token, value);
  }

  if (/{{[A-Z_]+}}/.test(content)) {
    throw new Error("Template contains unreplaced tokens; check .sentinel/templates/capsule.md");
  }
  return content.trimEnd() + "\n";
}

/**
 * @param {string[]} seeds
 */
const normalizeSeeds = (seeds) => seeds.filter(Boolean).map((entry) => entry.replace(/\\/g, "/"));

/**
 * @typedef {Object} GenerateCapsuleResult
 * @property {string} capsuleId
 * @property {string} content
 * @property {string} outPath
 */

/**
 * Generate capsule content for a given spec directory.
 * @param {object} params
 * @param {string} params.specDir Absolute path to the spec folder.
 * @param {string} params.decision Decision ID for ProducedBy header.
 * @param {string} [params.agent]
 * @param {string} [params.rulesHash]
 * @param {boolean} [params.write]
 * @param {string} [params.root]
 * @returns {Promise<GenerateCapsuleResult>}
 */
export async function generateCapsule({
  specDir,
  decision,
  agent = "ROUTER",
  rulesHash,
  write = true,
  root = REPO_ROOT
}) {
  if (!specDir) throw new Error("--spec is required");
  if (!decision) throw new Error("--decision is required");
  const resolved = path.resolve(specDir);
  const slug = path.basename(resolved);
  const specPath = path.join(resolved, "spec.md");
  const planPath = path.join(resolved, "plan.md");
  const tasksPath = path.join(resolved, "tasks.md");

  const [spec, plan, tasks] = await Promise.all([specPath, planPath, tasksPath].map((p) => readFile(p, "utf8")));

  const goalSection = extractSection(spec, "Goal");
  if (!goalSection) throw new Error("spec.md is missing a 'Goal' section");
  const goal = formatParagraph(goalSection);

  const requiredOutputs = extractList(extractSection(tasks, "Required Outputs"));
  if (!requiredOutputs.length) throw new Error("tasks.md must define bullet items under 'Required Outputs'");

  const acceptanceCriteria = extractList(extractSection(tasks, "Acceptance Criteria"));
  if (!acceptanceCriteria.length) throw new Error("tasks.md must define 'Acceptance Criteria'");

  const routerNotes = extractList(extractSection(plan, "Router Notes"));
  if (!routerNotes.length) throw new Error("plan.md must define 'Router Notes'");

  const contextSeedsSection = extractSection(plan, "Allowed Context Seeds");
  const contextSeeds = extractList(contextSeedsSection);

  const defaultSeeds = normalizeSeeds([
    path.relative(root, specPath),
    path.relative(root, planPath),
    path.relative(root, tasksPath),
    ...contextSeeds
  ]);

  const allowedContext = await buildAllowedContext({ root, seeds: defaultSeeds });

  const capsuleId = hashCapsuleId(slug, `${spec}\n${plan}\n${tasks}`);
  const header = renderHeader({
    agent,
    rulesHash: rulesHash || `${agent}@1.0`,
    decision
  });

  const content = await renderCapsule({
    PRODUCED_BY: header,
    CAPSULE_ID: capsuleId,
    GOAL: goal,
    REQUIRED_OUTPUTS: formatList(requiredOutputs),
    ACCEPTANCE_CRITERIA: formatList(acceptanceCriteria),
    ALLOWED_CONTEXT: formatList(allowedContext),
    ROUTER_NOTES: formatList(routerNotes)
  });

  const lineCount = content.split("\n").length;
  if (lineCount > MAX_LINES) {
    throw new Error(`Capsule exceeds ${MAX_LINES} lines (rendered ${lineCount})`);
  }

  const outPath = path.join(resolved, "capsule.md");
  if (write) {
    await writeFile(outPath, content, "utf8");
  }

  return { capsuleId, content, outPath };
}

async function main() {
  const specArgRaw = arg("--spec");
  if (typeof specArgRaw !== "string") die("--spec <path> is required");
  const decisionArg = arg("--decision");
  if (typeof decisionArg !== "string") die("--decision <D-####> is required");
  const agentArg = arg("--agent", "ROUTER");
  const agent = typeof agentArg === "string" ? agentArg : "ROUTER";
  const rulesHashArg = arg("--rulesHash");
  const rulesHash = typeof rulesHashArg === "string" ? rulesHashArg : undefined;
  const dryRun = hasFlag("--dry-run");

  const specDir = path.isAbsolute(specArgRaw) ? specArgRaw : path.resolve(process.cwd(), specArgRaw);
  const result = await generateCapsule({
    specDir,
    decision: decisionArg,
    agent,
    rulesHash,
    root: REPO_ROOT,
    write: !dryRun
  });

  if (dryRun) {
    process.stdout.write(result.content);
  } else {
    const rel = path.relative(REPO_ROOT, result.outPath);
    console.log(`capsule:create -> ${rel} (${result.capsuleId})`);
  }
}

const invokedDirectly = path.resolve(process.argv[1] || "") === __filename;

if (invokedDirectly) {
  main().catch((err) => {
    die(err?.message || String(err));
  });
}
