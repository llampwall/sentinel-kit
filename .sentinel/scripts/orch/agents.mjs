#!/usr/bin/env node
// @ts-check
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0011 */
/**
 * Agent registry helper used by the prompt renderer.
 * - Enumerates `.sentinel/agents/**`
 * - Validates agent.json + ROLE/PLAYBOOK markdown files
 * - Surfaces normalized metadata (role/playbook contents, mount paths, keywords)
 */

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../..");
const AGENTS_DIRNAME = ".sentinel/agents";

const REQUIRED_STRING_FIELDS = ["id", "name", "rulesHash", "summary"];
const REQUIRED_ARRAY_FIELDS = ["mount_paths", "prompt_files"];

/**
 * @typedef {Object} AgentPrompt
 * @property {string} path Relative path to the prompt file
 * @property {string} content Markdown content
 */

/**
 * @typedef {Object} AgentMetadata
 * @property {string} id
 * @property {string} name
 * @property {string} rulesHash
 * @property {string} summary
 * @property {string[]} routingKeywords
 * @property {string[]} mountPaths
 * @property {AgentPrompt[]} prompts
 * @property {AgentPrompt} role
 * @property {AgentPrompt} playbook
 * @property {string} dir Relative path to the agent directory
 */

/**
 * Load all agents under `.sentinel/agents/**`.
 * @param {{root?: string}} [options]
 * @returns {Promise<{ agents: AgentMetadata[]; lookup: Map<string, AgentMetadata> }>}
 */
export async function loadAgents(options = {}) {
  const root = options.root ? path.resolve(options.root) : ROOT;
  const agentsDir = path.resolve(root, AGENTS_DIRNAME);
  let dirents;
  try {
    dirents = await fs.readdir(agentsDir, { withFileTypes: true });
  } catch (error) {
    throw new Error(
      `Unable to read agent directory '${relativePath(root, agentsDir)}': ${formatError(error)}`
    );
  }

  const agents = [];
  const errors = [];
  for (const entry of dirents) {
    if (!entry.isDirectory()) continue;
    try {
      const agent = await loadAgentDirectory({ root, agentsDir, agentName: entry.name });
      agents.push(agent);
    } catch (error) {
      errors.push(`[${entry.name}] ${formatError(error)}`);
    }
  }

  if (errors.length) {
    throw new Error(`Agent discovery failed:\n${errors.join("\n")}`);
  }

  agents.sort((a, b) => a.id.localeCompare(b.id, undefined, { sensitivity: "base" }));
  const lookup = new Map(agents.map((agent) => [agent.id.toLowerCase(), agent]));
  return { agents, lookup };
}

/**
 * @param {{root: string; agentsDir: string; agentName: string}} params
 * @returns {Promise<AgentMetadata>}
 */
async function loadAgentDirectory({ root, agentsDir, agentName }) {
  const agentDir = path.join(agentsDir, agentName);
  const relativeDir = relativePath(root, agentDir);
  const agentJsonPath = path.join(agentDir, "agent.json");
  const agentConfig = await readJson(agentJsonPath);

  const missingFields = REQUIRED_STRING_FIELDS.filter((field) => !isNonEmptyString(agentConfig[field]));
  if (missingFields.length) {
    throw new Error(`agent.json missing required string fields: ${missingFields.join(", ")}`);
  }

  const arrayIssues = REQUIRED_ARRAY_FIELDS.filter(
    (field) => !Array.isArray(agentConfig[field]) || !agentConfig[field].every(isNonEmptyString)
  );
  if (arrayIssues.length) {
    throw new Error(`agent.json fields must be string arrays: ${arrayIssues.join(", ")}`);
  }

  if (agentConfig.id !== agentName) {
    throw new Error(`agent id '${agentConfig.id}' must match directory name '${agentName}'`);
  }

  const promptFiles = /** @type {string[]} */ (agentConfig.prompt_files);
  const prompts = [];
  for (const relPath of promptFiles) {
    const absPath = path.resolve(root, relPath);
    const content = await readUtf8(absPath);
    prompts.push({
      path: normalizePath(relativePath(root, absPath)),
      content: content.trim()
    });
  }

  const rolePrompt = findPrompt(prompts, "ROLE");
  const playbookPrompt = findPrompt(prompts, "PLAYBOOK");
  if (!rolePrompt || !playbookPrompt) {
    throw new Error("prompt_files must include ROLE.md and PLAYBOOK.md entries");
  }

  return {
    id: agentConfig.id,
    name: agentConfig.name,
    rulesHash: agentConfig.rulesHash,
    summary: agentConfig.summary,
    routingKeywords: Array.isArray(agentConfig.routing_keywords)
      ? agentConfig.routing_keywords.filter(isNonEmptyString)
      : [],
    mountPaths: /** @type {string[]} */ (agentConfig.mount_paths).map((p) => normalizePath(p)),
    prompts,
    role: rolePrompt,
    playbook: playbookPrompt,
    dir: normalizePath(relativeDir)
  };
}

/**
 * @param {string} p
 */
async function readJson(p) {
  try {
    const raw = await fs.readFile(p, "utf8");
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`Failed to read/parse JSON '${p}': ${formatError(error)}`);
  }
}

/**
 * @param {string} p
 */
async function readUtf8(p) {
  try {
    return await fs.readFile(p, "utf8");
  } catch (error) {
    throw new Error(`Unable to read '${p}': ${formatError(error)}`);
  }
}

/**
 * @param {unknown} value
 */
function isNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

/**
 * @param {string} root
 * @param {string} target
 */
function relativePath(root, target) {
  return path.relative(root, target);
}

/**
 * @param {string} p
 */
function normalizePath(p) {
  return p.split(path.sep).join("/");
}

/**
 * @param {AgentPrompt[]} prompts
 * @param {string} needle
 * @returns {AgentPrompt | undefined}
 */
function findPrompt(prompts, needle) {
  return prompts.find((prompt) => prompt.path.toLowerCase().includes(needle.toLowerCase()));
}

/**
 * @param {unknown} error
 */
function formatError(error) {
  return error instanceof Error ? error.message : String(error);
}

export default {
  loadAgents
};
