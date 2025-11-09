#!/usr/bin/env node
/* ProducedBy=BUILDER RulesHash=BUILDER@1.1 Decision=D-0011 */
/**
 * Eta-powered prompt renderer.
 * - Router mode renders the router ROLE/PLAYBOOK + capsule context and agent roster.
 * - Capsule mode renders the selected agent's ROLE/PLAYBOOK with capsule context.
 *
 * Usage:
 *   node scripts/orch/prompt-render.mjs --mode router --capsule <path> [--output prompt.md]
 *   node scripts/orch/prompt-render.mjs --mode capsule --capsule <path> --agent <id> [--output prompt.md]
 */

import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Eta } from "eta";
import Ajv from "ajv";
import addFormats from "ajv-formats";
import crypto from "node:crypto";
import { loadAgents } from "./agents.mjs";
import { extractListFromHeading } from "../lib/capsule-md.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../..");
const ROUTER_TEMPLATE = ".sentinel/prompts/router.prompt.eta.md";
const AGENT_TEMPLATE = ".sentinel/prompts/agent.prompt.eta.md";
const ROUTER_LOG_DIR = ".sentinel/router_log";
const templateCache = new Map();
const eta = new Eta({ autoEscape: false });
const ajv = addFormats(new Ajv({ allErrors: true, strict: false }));
const lintedCapsules = new Set();
let lintModulePromise;
const routerSchema = ajv.compile({
  type: "object",
  properties: {
    leadAgent: { type: "string", minLength: 1 },
    requiredOutputs: { type: "array", minItems: 1, items: { type: "string", minLength: 1 } },
    acceptanceCriteria: { type: "array", items: { type: "string" } },
    contextToMount: { type: "array", minItems: 1, items: { type: "string", minLength: 1 } },
    notes: { type: "string" }
  },
  required: ["leadAgent", "requiredOutputs", "contextToMount"],
  additionalProperties: false
});

const MODES = {
  router: "router",
  capsule: "capsule"
};

/**
 * @typedef {Object} PromptArgs
 * @property {"router"|"capsule"} mode
 * @property {string} capsule
 * @property {string | undefined} agent
 * @property {string | undefined} output
 * @property {string | undefined} routerJson
 */

/**
 * @typedef {Object} CapsuleContext
 * @property {string} path
 * @property {string} content
 * @property {string[]} allowedContext
 */

export function parseArgs(argv = process.argv.slice(2)) {
  const out = /** @type {PromptArgs} */ ({
    mode: undefined,
    capsule: undefined,
    agent: undefined,
    output: undefined,
    routerJson: undefined
  });

  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const value = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : undefined;
    switch (token) {
      case "--mode":
        out.mode = validateMode(value);
        break;
      case "--capsule":
        out.capsule = requireValue(token, value);
        break;
      case "--agent":
        out.agent = requireValue(token, value);
        break;
      case "--output":
        out.output = requireValue(token, value);
        break;
      case "--router-json":
        out.routerJson = requireValue(token, value);
        break;
      default:
        throw new Error(`Unknown flag '${token}'`);
    }
  }

  if (!out.mode) throw new Error("--mode is required");
  if (!out.capsule) throw new Error("--capsule is required");
  if (out.mode === MODES.capsule && !out.agent) {
    throw new Error("--agent is required when --mode capsule");
  }
  return out;
}

function validateMode(value) {
  if (!value || !Object.hasOwn(MODES, value)) {
    throw new Error("--mode must be 'router' or 'capsule'");
  }
  return value;
}

function requireValue(flag, value) {
  if (!value) throw new Error(`${flag} requires a value`);
  return value;
}

/**
 * @param {PromptArgs} args
 */
async function main(args) {
  if (args.mode === MODES.router) {
    const prompt = await renderRouterPrompt({
      capsulePath: args.capsule
    });
    await writeOutput(prompt, args.output);
    if (args.routerJson) {
      const payload = await readJsonInput(args.routerJson);
      validateRouterPayload(payload);
      const logPath = await writeRouterLog({
        capsulePath: args.capsule,
        payload
      });
      console.error(`router log -> ${normalizePath(path.relative(ROOT, logPath))}`);
    }
    return;
  }

  const prompt = await renderCapsulePrompt({
    capsulePath: args.capsule,
    agentId: args.agent
  });
  await writeOutput(prompt, args.output);
}

async function writeOutput(content, outputPath) {
  if (!outputPath) {
    process.stdout.write(content);
    return;
  }
  const abs = path.isAbsolute(outputPath) ? outputPath : path.resolve(ROOT, outputPath);
  await fs.mkdir(path.dirname(abs), { recursive: true });
  await fs.writeFile(abs, content, "utf8");
}

async function readJsonInput(inputPath) {
  const abs = path.isAbsolute(inputPath) ? inputPath : path.resolve(ROOT, inputPath);
  const raw = await fs.readFile(abs, "utf8");
  return JSON.parse(raw);
}

/**
 * @param {{ capsulePath: string, root?: string }} options
 */
export async function renderRouterPrompt({ capsulePath, root = ROOT }) {
  const capsule = await buildCapsuleContext({ capsulePath, root });
  const { agents, lookup } = await loadAgents({ root });
  const router = lookup.get("router");
  if (!router) throw new Error("Router agent not found in registry");

  const template = await loadTemplate(path.resolve(root, ROUTER_TEMPLATE));
  return eta.renderString(template, {
    router: {
      role: router.role.content,
      playbook: router.playbook.content
    },
    capsule,
    agents: agents.map((agent) => ({
      id: agent.id,
      name: agent.name,
      rulesHash: agent.rulesHash,
      summary: agent.summary,
      routingKeywords: agent.routingKeywords
    }))
  });
}

/**
 * @param {{ capsulePath: string, agentId: string, root?: string }} options
 */
export async function renderCapsulePrompt({ capsulePath, agentId, root = ROOT }) {
  if (!agentId) throw new Error("agentId is required");
  const capsule = await buildCapsuleContext({ capsulePath, root });
  const { lookup } = await loadAgents({ root });
  const agent = lookup.get(agentId.toLowerCase());
  if (!agent) {
    throw new Error(`Agent '${agentId}' not found. Available: ${Array.from(lookup.keys()).join(", ")}`);
  }

  const template = await loadTemplate(path.resolve(root, AGENT_TEMPLATE));
  return eta.renderString(template, {
    agent: {
      id: agent.id,
      name: agent.name,
      rulesHash: agent.rulesHash,
      role: agent.role.content,
      playbook: agent.playbook.content,
      mountPaths: agent.mountPaths
    },
    capsule
  });
}

/**
 * @param {{ capsulePath: string, root?: string }} options
 * @returns {Promise<CapsuleContext>}
 */
export async function buildCapsuleContext({ capsulePath, root = ROOT }) {
  const abs = path.isAbsolute(capsulePath) ? capsulePath : path.resolve(root, capsulePath);
  await lintCapsuleAllowedContext({ capsuleAbs: abs, root });
  const content = await fs.readFile(abs, "utf8");
  const allowedContext = extractListFromHeading(content, "Allowed Context");
  return {
    path: normalizePath(path.relative(root, abs)),
    content: content.trim(),
    allowedContext
  };
}

async function loadTemplate(p) {
  const cached = templateCache.get(p);
  if (cached) return cached;
  const tpl = await fs.readFile(p, "utf8");
  templateCache.set(p, tpl);
  return tpl;
}

function normalizePath(p) {
  return p.split(path.sep).join("/");
}

export function validateRouterPayload(payload) {
  const valid = routerSchema(payload);
  if (!valid) {
    const message = ajv.errorsText(routerSchema.errors, { separator: "\n" });
    throw new Error(`Router payload failed schema validation:\n${message}`);
  }
}

export async function writeRouterLog({ capsulePath, payload, root = ROOT }) {
  const absCapsule = path.isAbsolute(capsulePath) ? capsulePath : path.resolve(root, capsulePath);
  const capsuleRel = normalizePath(path.relative(root, absCapsule));
  const slug = path.basename(path.dirname(absCapsule)) || path.basename(absCapsule);
  const capsuleHash = crypto.createHash("sha256").update(capsuleRel).digest("hex").slice(0, 8);
  const timestamp = new Date().toISOString();
  const fileName = `${timestamp.replace(/[:]/g, "").replace(/\..+$/, "")}-${slug}.jsonl`;
  const logDir = path.resolve(root, ROUTER_LOG_DIR);
  await fs.mkdir(logDir, { recursive: true });
  const record = {
    timestamp,
    capsule: capsuleRel,
    capsuleHash,
    payload
  };
  const logPath = path.join(logDir, fileName);
  await fs.writeFile(logPath, `${JSON.stringify(record)}\n`, "utf8");
  return logPath;
}

async function cli() {
  try {
    const args = parseArgs();
    await main(args);
  } catch (error) {
    console.error(error?.message || error);
    process.exit(1);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  cli();
}

export default {
  parseArgs,
  renderRouterPrompt,
  renderCapsulePrompt,
  buildCapsuleContext,
  validateRouterPayload,
  writeRouterLog
};

async function lintCapsuleAllowedContext({ capsuleAbs, root }) {
  if (lintedCapsules.has(capsuleAbs)) return;
  const module = await loadLintModule();
  const rel = normalizePath(path.relative(root, capsuleAbs));
  const summary = await module.lintContext({
    root,
    include: [rel]
  });
  const errors = summary.issues.filter((issue) => issue.severity === "error");
  if (errors.length) {
    const formatted = errors.map((issue) => `- [${issue.code}] ${issue.message}`).join("\n");
    throw new Error(`Allowed Context validation failed for ${rel}:\n${formatted}`);
  }
  const warnings = summary.issues.filter((issue) => issue.severity === "warning");
  if (warnings.length) {
    const formatted = warnings.map((issue) => `- [${issue.code}] ${issue.message}`).join("\n");
    console.warn(`Allowed Context warnings for ${rel}:\n${formatted}`);
  }
  lintedCapsules.add(capsuleAbs);
}

async function loadLintModule() {
  if (!lintModulePromise) {
    try {
      await import("tsx/esm");
    } catch (error) {
      throw new Error(`Failed to load tsx runtime for context linter: ${error instanceof Error ? error.message : String(error)}`);
    }
    lintModulePromise = import("../context/lint.mts");
  }
  return lintModulePromise;
}
