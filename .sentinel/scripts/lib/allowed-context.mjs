// @ts-check
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0010 */
/**
 * Allowed Context discovery + validation.
 * - Scans `.sentinel/context/**` to auto-include shared background docs.
 * - Normalizes requested include paths, verifies they exist (or have a valid base when globs are used),
 *   and ensures nothing escapes the repo root.
 * - Returns a deterministic, de-duplicated list consumed by the capsule generator.
 */

import { readdir, stat } from "node:fs/promises";
import path from "node:path";

const DEFAULT_CONTEXT_DIR = ".sentinel/context";
const EXCLUDED_SUBPATHS = new Set(["limits"]);

/**
 * @param {string} p
 */
const posixify = (p) => p.replace(/\\/g, "/");

/**
 * Recursively list context files relative to repo root.
 * Missing directories simply resolve to an empty list.
 * @param {string} root
 * @param {string} [contextDir]
 */
export async function listContextFiles(root, contextDir = DEFAULT_CONTEXT_DIR) {
  const resolved = path.resolve(root, contextDir);
  /** @type {string[]} */
  const entries = [];

  /**
   * @param {string} dir
   */
  async function walk(dir) {
    let dirents;
    try {
      dirents = await readdir(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of dirents) {
      const abs = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        const relative = posixify(path.relative(resolved, abs));
        const topLevel = relative.split("/")[0] ?? relative;
        if (EXCLUDED_SUBPATHS.has(topLevel)) {
          continue;
        }
        await walk(abs);
      } else {
        entries.push(abs);
      }
    }
  }

  try {
    const info = await stat(resolved);
    if (!info.isDirectory()) return [];
  } catch {
    return [];
  }

  await walk(resolved);

  return entries
    .map((abs) => posixify(path.relative(root, abs)))
    .sort((a, b) => a.localeCompare(b));
}

/**
 * Remove leading ./, collapse duplicate slashes, and guard escape attempts.
 * @param {string} root
 * @param {string} raw
 */
export function normalizeInclude(root, raw) {
  if (!raw || typeof raw !== "string") {
    throw new Error("Allowed Context entry must be a non-empty string");
  }
  let cleaned = raw.trim().replace(/\\/g, "/");
  cleaned = cleaned.replace(/^\.\/+/, "");
  cleaned = cleaned.replace(/\/{2,}/g, "/");
  if (cleaned === "") throw new Error("Allowed Context entry cannot be empty");

  const base = globBase(cleaned);
  const resolved = path.resolve(root, base || ".");
  const rel = path.relative(root, resolved);
  if (rel.startsWith("..")) {
    throw new Error(`Allowed Context entry escapes repo root: ${raw}`);
  }

  return cleaned;
}

/**
 * @param {string} p
 */
function globBase(p) {
  if (!p.includes("*")) return p;
  const idx = p.indexOf("*");
  const slice = p.slice(0, idx);
  const trimmed = slice.replace(/\/$/, "");
  return trimmed || ".";
}

/**
 * Ensure the normalized include path points to an existing file/dir (or a valid glob base).
 * @param {string} root
 * @param {string} normalized
 */
export async function assertIncludeExists(root, normalized) {
  const hasGlob = normalized.includes("*");
  const target = hasGlob ? globBase(normalized) : normalized;
  if (!target || target === ".") return;
  const resolved = path.resolve(root, target);
  try {
    await stat(resolved);
  } catch {
    throw new Error(`Allowed Context entry does not exist: ${normalized}`);
  }
}

/**
 * Build the final Allowed Context list (context docs + requested seeds).
 * @param {object} params
 * @param {string} params.root
 * @param {string[]} [params.seeds]
 */
export async function buildAllowedContext({ root, seeds = [] }) {
  if (!root) throw new Error("Repo root is required for Allowed Context generation");
  const defaults = await listContextFiles(root);

  /** @type {string[]} */
  const extras = [];
  for (const raw of seeds) {
    const normalized = normalizeInclude(root, raw);
    await assertIncludeExists(root, normalized);
    extras.push(normalized);
  }

  const merged = [...defaults, ...extras];
  const unique = Array.from(new Set(merged));
  unique.sort((a, b) => a.localeCompare(b));
  return unique;
}

export default {
  listContextFiles,
  normalizeInclude,
  assertIncludeExists,
  buildAllowedContext
};
