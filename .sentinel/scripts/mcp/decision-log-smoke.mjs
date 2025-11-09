#!/usr/bin/env node
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  StreamMessageReader,
  StreamMessageWriter
} from "vscode-jsonrpc/node.js";
import { createMessageConnection } from "vscode-jsonrpc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../..");
const SERVER = path.join(ROOT, ".sentinel", "scripts", "mcp", "decision-log.mjs");

const SAMPLE_ARGS = {
  author: "Smoke",
  scope: ["README.md"],
  summary: "Smoke Entry",
  rationale: "validate MCP server",
  outputs: ["README.md"]
};

async function smoke() {
const child = spawn(process.execPath, [SERVER], {
  cwd: ROOT,
  env: {
    ...process.env,
    SENTINEL_DECISION_LOG_DRY_RUN: "1"
  },
  stdio: ["pipe", "pipe", "inherit"]
});
  const connection = createMessageConnection(
    new StreamMessageReader(child.stdout),
    new StreamMessageWriter(child.stdin)
  );
  connection.listen();
  try {
    await connection.sendRequest("initialize", {
      protocolVersion: "2024-11-01",
      capabilities: {},
      clientInfo: { name: "smoke", version: "0.0.0" }
    });
    connection.sendNotification("notifications/initialized");
    const tools = await connection.sendRequest("tools/list", {});
    if (!tools?.tools?.some((tool) => tool.name === "decision_log_append")) {
      throw new Error("decision_log_append tool missing from tools/list");
    }
    const response = await connection.sendRequest("tools/call", {
      name: "decision_log_append",
      arguments: SAMPLE_ARGS
    });
    if (response.isError) {
      console.error("decision_log response", response);
      throw new Error("decision_log_append returned error");
    }
    console.log("decision_log smoke test passed.");
  } finally {
    connection.dispose();
    child.kill();
  }
}

smoke().catch((error) => {
  console.error(error?.message || error);
  process.exit(1);
});



