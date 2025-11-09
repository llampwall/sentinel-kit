#!/usr/bin/env node
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0016 */
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import { createMcpServer } from "./lib/bootstrap.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SENTINEL_DIR = path.resolve(__dirname, "..", "..");
const NODE_BIN = process.execPath;
const VITEST_CLI = path.join(
  SENTINEL_DIR,
  "node_modules",
  "vitest",
  "dist",
  "cli.js"
);

const SENTINEL_RUN_SCHEMA = z.object({
  filter: z.string().min(1).optional()
});

function parseJsonOutput(output) {
  const trimmed = output.trim();
  if (!trimmed) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    const idx = trimmed.lastIndexOf("\n{");
    if (idx !== -1) {
      try {
        return JSON.parse(trimmed.slice(idx + 1));
      } catch {
        return null;
      }
    }
  }
  return null;
}

async function executeSentinelTests(args) {
  const cliArgs = ["run", "--config", "vitest.config.sentinel.ts", "--reporter=json"];
  if (args.filter) {
    cliArgs.push("--testNamePattern", args.filter);
  }

  return new Promise((resolve, reject) => {
    const child = spawn(NODE_BIN, [VITEST_CLI, ...cliArgs], {
      cwd: SENTINEL_DIR,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";

    child.stdout?.setEncoding("utf8");
    child.stdout?.on("data", (chunk) => {
      stdout += chunk;
    });

    child.stderr?.setEncoding("utf8");
    child.stderr?.on("data", (chunk) => {
      stderr += chunk;
    });

    child.on("error", reject);
    child.on("close", (code) => {
      resolve({ code, stdout, stderr, summary: parseJsonOutput(stdout) });
    });
  });
}

if (process.env.SENTINEL_RUN_DEBUG) {
  console.error("[sentinel-run] vitest cli:", VITEST_CLI);
}

const defaultExecutor = executeSentinelTests;
let executor = defaultExecutor;

export function __setSentinelExecutor(fn) {
  executor = fn;
}

export function __resetSentinelExecutor() {
  executor = defaultExecutor;
}

export async function runSentinelTool(args) {
  const { code, stdout, stderr, summary } = await executor(args);
  const ok = code === 0 && summary?.success !== false;
  return {
    ok,
    content: [
      {
        type: "json",
        json: {
          ok,
          exitCode: code,
          summary,
          stdout,
          stderr
        }
      }
    ]
  };
}

export function createSentinelServer() {
  return createMcpServer({
    name: "sentinel-run",
    version: "0.1.0",
    tools: [
      {
        name: "sentinel_run",
        description: "Run sentinel regression tests via vitest",
        schema: SENTINEL_RUN_SCHEMA,
        handler: runSentinelTool
      }
    ]
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  createSentinelServer();
}

export default {
  createSentinelServer,
  runSentinelTool,
  __setSentinelExecutor,
  __resetSentinelExecutor
};




