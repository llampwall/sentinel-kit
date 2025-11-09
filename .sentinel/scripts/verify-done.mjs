#!/usr/bin/env node
// Simple "prove it" gate for task completion.
// Usage:
//   node .sentinel/scripts/verify-done.mjs --task 6.4
//   node .sentinel/scripts/verify-done.mjs --paths ".sentinel/scripts/orch/prompt-render.smoke.mjs" --cmd "pnpm -C .sentinel test"
// Exit 0 = verified, Exit 1 = failed.

import { exec as _exec } from "node:child_process";
import { access } from "node:fs/promises";
import { constants as FS } from "node:fs";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const exec = (cmd) =>
  new Promise((res) => {
    _exec(cmd, { windowsHide: true, maxBuffer: 1024 * 1024 }, (err, stdout, stderr) =>
      res({ code: err ? 1 : 0, stdout, stderr })
    );
  });

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "../../..");
const manifestPath = resolve(repoRoot, ".sentinel/tasks/proofs.json");

const argv = process.argv.slice(2);
const getFlag = (name) => {
  const i = argv.indexOf(`--${name}`);
  return i === -1 ? null : argv[i + 1] ?? "";
};

const taskId = getFlag("task");
const adhocPaths = (getFlag("paths") || "").split("|").map(s => s.trim()).filter(Boolean);
const adhocCmds  = (getFlag("cmd")   || "").split("|").map(s => s.trim()).filter(Boolean);

const fail = (msg) => {
  console.error(`✖ verify-done: ${msg}`);
  process.exit(1);
};
const ok = (msg) => {
  console.log(`✔ verify-done: ${msg}`);
};

const fileExists = async (p) => {
  try { await access(p, FS.F_OK); return true; } catch { return false; }
};

const loadManifest = async () => {
  try {
    const raw = await readFile(manifestPath, "utf8");
    return JSON.parse(raw);
  } catch {
    return { tasks: {} };
  }
};

const main = async () => {
  const manifest = await loadManifest();
  let paths = adhocPaths;
  let cmds  = adhocCmds;

  if (taskId) {
    const def = manifest.tasks?.[taskId];
    if (!def) fail(`no manifest entry for task "${taskId}" in ${manifestPath}`);
    paths = paths.length ? paths : def.paths || [];
    cmds  = cmds.length  ? cmds  : def.cmds  || [];
  }
  if (!paths.length && !cmds.length) {
    fail("nothing to verify (provide --task or --paths/--cmd)");
  }

  // 1) Path checks (all must exist)
  for (const rel of paths) {
    const abs = resolve(repoRoot, rel);
    const exists = await fileExists(abs);
    if (!exists) fail(`missing expected file: ${rel}`);
    ok(`found ${rel}`);
  }

  // 2) Command checks (all must succeed)
  for (const cmd of cmds) {
    console.log(`$ ${cmd}`);
    const { code, stdout, stderr } = await exec(cmd);
    process.stdout.write(stdout || "");
    process.stderr.write(stderr || "");
    if (code !== 0) fail(`command failed: ${cmd}`);
    ok(`command ok: ${cmd}`);
  }

  // 3) (Optional) ensure there are committed changes for “done” claims
  //    Skip if running inside CI or if no taskId (can toggle via env).
  if (!process.env.SKIP_GIT_CHECK) {
    const { code, stdout } = await exec("git status --porcelain");
    if (code === 0 && stdout.trim().length === 0) {
      ok("git working tree clean (no uncommitted junk)");
    }
  }

  console.log("✅ verified");
  process.exit(0);
};

main().catch((e) => fail(e?.message || String(e)));
