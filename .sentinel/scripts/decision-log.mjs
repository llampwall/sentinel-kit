#!/usr/bin/env node
import fs from "fs";
import fsp from "fs/promises";
import path from "path";
import readline from "readline";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");
const LEDGER_PATH = path.join(ROOT, "DECISIONS.md");

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {};
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg.startsWith("--")) {
      const key = arg.replace(/^--/, "");
      options[key] = args[i + 1];
      i += 1;
    }
  }
  return options;
}

async function readLedger() {
  return fsp.readFile(LEDGER_PATH, "utf8");
}

function nextIdFromContent(content) {
  const match = content.match(/## NEXT_ID\s+([A-Z]-\d{4})/);
  if (!match) throw new Error("NEXT_ID not found in DECISIONS.md");
  return match[1];
}

function bumpNextId(id) {
  const [prefix, num] = id.split("-");
  const nextNum = Number.parseInt(num, 10) + 1;
  return `${prefix}-${nextNum.toString().padStart(4, "0")}`;
}

function renderEntry({ id, author, date, scope, decision, rationale, supersedes }) {
  return [
    `ID: ${id}`,
    `Date: ${date}`,
    `Author: ${author}`,
    `Scope: ${scope}`,
    `Decision: ${decision}`,
    `Rationale: ${rationale}`,
    `Supersedes: ${supersedes || "none"}`
  ].join("\n") + "\n";
}

async function writeLedger(content, entry, nextId) {
  const updated = content.replace(
    /(## NEXT_ID\s+[A-Z]-\d{4})/,
    `## NEXT_ID\n${nextId}`
  );
  const final = updated.trimEnd() + "\n\n" + entry;
  await fsp.writeFile(LEDGER_PATH, final, "utf8");
}

async function main() {
  const opts = parseArgs();
  const required = ["author", "date", "scope", "decision", "rationale"];
  for (const key of required) {
    if (!opts[key]) {
      throw new Error(`Missing required argument --${key}`);
    }
  }

  const content = await readLedger();
  const id = nextIdFromContent(content);
  const entry = renderEntry({
    id,
    author: opts.author,
    date: opts.date,
    scope: opts.scope,
    decision: opts.decision,
    rationale: opts.rationale,
    supersedes: opts.supersedes
  });
  const nextId = bumpNextId(id);
  await writeLedger(content, entry, nextId);

  const producedBy = `ProducedBy=${opts.author.toUpperCase()} RulesHash=${opts.author.toUpperCase()}@1.0 Decision=${id}`;
  console.log(
    JSON.stringify(
      { id, ledgerPath: LEDGER_PATH, producedBy },
      null,
      2
    )
  );
}

main().catch((err) => {
  console.error(err?.message || err);
  process.exit(1);
});
