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
const SERVER = path.join(ROOT, ".sentinel", "scripts", "mcp", "sentinel-run.mjs");

async function smoke() {
  const child = spawn(process.execPath, [SERVER], {
    cwd: ROOT,
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
    if (!tools?.tools?.some((tool) => tool.name === "sentinel_run")) {
      throw new Error("sentinel_run tool missing from tools/list");
    }
    const response = await connection.sendRequest("tools/call", {
      name: "sentinel_run",
      arguments: { filter: "capsule" }
    });
    if (response.isError) {
      console.error("sentinel_run response", response);
      throw new Error("sentinel_run returned error");
    }
    console.log("sentinel_run smoke test passed.");
  } finally {
    connection.dispose();
    child.kill();
  }
}

smoke().catch((error) => {
  console.error(error?.message || error);
  process.exit(1);
});

