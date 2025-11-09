#!/usr/bin/env node
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0017 */
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import { createMcpServer } from "./lib/bootstrap.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SENTINEL_DIR = path.resolve(__dirname, "..", "..");
const NODE_BIN = process.execPath;
const DECISION_LOG_CLI = path.join(SENTINEL_DIR, "scripts", "decision-log.mjs");
const DRY_RUN_ENV = "SENTINEL_DECISION_LOG_DRY_RUN";

const DECISION_LOG_SCHEMA = z.object({
  author: z.string().min(1),
  scope: z.array(z.string().min(1)).min(1),
  summary: z.string().min(1),
  rationale: z.string().min(1),
  outputs: z.array(z.string().min(1)).min(1)
});

function buildCliArgs(args) {
  return [
    DECISION_LOG_CLI,
    `--author=${args.author}`,
    `--scope=${args.scope.join(",")}`,
    `--summary=${args.summary}`,
    `--rationale=${args.rationale}`,
    `--outputs=${args.outputs.join(",")}`
  ];
}

function spawnDecisionLog(args) {
  return new Promise((resolve, reject) => {
    const child = spawn(NODE_BIN, buildCliArgs(args), {
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
      if (code !== 0) {
        reject(new Error(stderr || "decision-log CLI failed"));
      } else {
        try {
          resolve(JSON.parse(stdout));
        } catch (error) {
          reject(new Error(`Unable to parse decision-log output: ${error?.message || error}`));
        }
      }
    });
  });
}

export async function appendDecision(args) {
  if (process.env[DRY_RUN_ENV] === "1") {
    return {
      ok: true,
      content: [
        {
          type: "json",
          json: {
            id: "D-DRY-RUN",
            args
          }
        }
      ]
    };
  }
  const payload = await spawnDecisionLog(args);
  return {
    ok: true,
    content: [
      {
        type: "json",
        json: payload
      }
    ]
  };
}

export function createDecisionLogServer() {
  return createMcpServer({
    name: "decision-log",
    version: "0.1.0",
    tools: [
      {
        name: "decision_log_append",
        description: "Append entries to the decisions ledger via the existing CLI",
        schema: DECISION_LOG_SCHEMA,
        handler: appendDecision
      }
    ]
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  createDecisionLogServer();
}

export default {
  createDecisionLogServer,
  appendDecision
};
