#!/usr/bin/env node
import fs from "node:fs";
import fsp from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, ".." );
const DEFAULT_LEDGER = path.join(ROOT, "DECISIONS.md");

function parseArgs(argv = process.argv.slice(2)) {
  const opts = {
    outputs: [],
    supersedes: "none"
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];

    if (key === "outputs") {
      if (next && !next.startsWith("--")) {
        opts.outputs.push(next);
        i += 1;
      }
      continue;
    }

    if (next && !next.startsWith("--")) {
      opts[key] = next;
      i += 1;
    } else {
      opts[key] = true;
    }
  }

  return opts;
}

function requireOption(value, label) {
  if (!value || !String(value).trim()) {
    throw new Error(`Missing required option --${label}`);
  }
  return String(value).trim();
}

function normalizeOutputs(list) {
  if (!list.length) throw new Error("Missing required option --outputs");
  return list
    .flatMap((item) => String(item).split(","))
    .map((entry) => entry.trim())
    .filter(Boolean)
    .join(", ");
}

async function readLedger(ledgerPath) {
  return fsp.readFile(ledgerPath, "utf8");
}

function extractNextId(content) {
  const match = content.match(/## NEXT_ID\s*([\r\n]+)([A-Z]-\d{4})/);
  if (!match) throw new Error("NEXT_ID block not found in DECISIONS.md");
  return match[2];
}

function bumpId(id) {
  const [prefix, number] = id.split("-");
  const next = (Number.parseInt(number, 10) + 1).toString().padStart(4, "0");
  return `${prefix}-${next}`;
}

function getGitShortHash(cwd) {
  try {
    const result = spawnSync("git", ["rev-parse", "--short", "HEAD"], {
      cwd,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"]
    });
    if (result.status === 0) {
      return result.stdout.trim() || "unknown";
    }
  } catch {
    /* ignore */
  }
  return "unknown";
}

function buildEntry({ id, date, author, scope, decision, rationale, outputs, supersedes }) {
  return [
    `ID: ${id}`,
    `Date: ${date}`,
    `Author: ${author}`,
    `Scope: ${scope}`,
    `Decision: ${decision}`,
    `Rationale: ${rationale}`,
    `Outputs: ${outputs}`,
    `Supersedes: ${supersedes || "none"}`
  ].join("\n");
}

async function acquireLock(lockPath) {
  try {
    const handle = await fsp.open(lockPath, fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_WRONLY);
    await handle.write(`${process.pid}\n`);
    return handle;
  } catch {
    throw new Error(`Decision ledger is locked (${lockPath}). Please retry after the current writer finishes.`);
  }
}

async function releaseLock(handle, lockPath) {
  try {
    await handle.close();
  } finally {
    await fsp.unlink(lockPath).catch(() => {});
  }
}

async function writeLedger(ledgerPath, nextId, entry, content) {
  const updatedHeader = content.replace(/(## NEXT_ID\s*)([A-Z]-\d{4})/, `$1${nextId}`);
  const final = `${updatedHeader.trimEnd()}\n\n${entry}\n`;
  await fsp.writeFile(ledgerPath, final, "utf8");
}

function buildSnippets({ agent, rulesHash, id, gitHash }) {
  const plain = `ProducedBy=${agent} RulesHash=${rulesHash} Decision=${id} (#${gitHash})`;
  return {
    plain,
    javascript: `/* ${plain} */`,
    python: `# ${plain}`,
    markdown: `<!-- ${plain} -->`
  };
}

async function main() {
  const opts = parseArgs();
  const ledgerPath = path.resolve(opts.ledger || DEFAULT_LEDGER);
  const lockPath = `${ledgerPath}.lock`;

  const author = requireOption(opts.author, "author");
  const scope = requireOption(opts.scope, "scope");
  const decision = requireOption(opts.summary || opts.decision, "summary");
  const rationale = requireOption(opts.rationale, "rationale");
  const outputs = normalizeOutputs(opts.outputs);
  const supersedes = opts.supersedes ? String(opts.supersedes) : "none";
  const date = opts.date ? requireOption(opts.date, "date") : new Date().toISOString().slice(0, 10);
  const agent = (opts.agent || author).toUpperCase();
  const rulesHash = opts.rulesHash || `${agent}@1.0`;

  const lockHandle = await acquireLock(lockPath);
  try {
    const content = await readLedger(ledgerPath);
    const currentId = extractNextId(content);
    const nextId = bumpId(currentId);

    const entry = buildEntry({
      id: currentId,
      date,
      author,
      scope,
      decision,
      rationale,
      outputs,
      supersedes
    });

    await writeLedger(ledgerPath, nextId, entry, content);

    const gitHash = getGitShortHash(path.dirname(ledgerPath));
    const snippets = buildSnippets({ agent, rulesHash, id: currentId, gitHash });
    const payload = {
      id: currentId,
      ledgerPath,
      snippets
    };
    process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
  } finally {
    await releaseLock(lockHandle, lockPath);
  }
}

main().catch((err) => {
  console.error(err?.message || err);
  process.exit(1);
});
