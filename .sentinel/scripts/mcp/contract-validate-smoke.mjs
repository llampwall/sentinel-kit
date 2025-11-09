#!/usr/bin/env node
/**
 * Smoke test for the contract_validate MCP server. Spins up the server,
 * performs initialize -> tools/list -> tools/call, and exits non-zero if
 * any step fails.
 */

import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  createMessageConnection,
  StreamMessageReader,
  StreamMessageWriter
} from "vscode-jsonrpc/node.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../..");
const SERVER = path.join(ROOT, ".sentinel", "scripts", "mcp", "contract-validate-server.mjs");

async function main() {
  const server = spawn(process.execPath, [SERVER], {
    cwd: ROOT,
    stdio: ["pipe", "pipe", "inherit"]
  });

  const connection = createMessageConnection(
    new StreamMessageReader(server.stdout),
    new StreamMessageWriter(server.stdin)
  );

  connection.listen();

  let closed = false;
  let completed = false;
  server.on("exit", (code) => {
    closed = true;
    if (!completed && code !== 0) {
      console.error("Smoke test failed: server exited unexpectedly.");
      process.exit(1);
    }
  });

  const init = await connection.sendRequest("initialize", {
    protocolVersion: "2024-11-01",
    capabilities: {},
    clientInfo: { name: "smoke-client", version: "0.0.0" }
  });
  if (!init?.serverInfo?.name) {
    throw new Error("Smoke test failed: initialize response missing serverInfo.");
  }

  connection.sendNotification("notifications/initialized");
  const list = await connection.sendRequest("tools/list", {});
  const toolNames = list?.tools?.map((tool) => tool.name) ?? [];
  if (!toolNames.includes("contract_validate")) {
    throw new Error("Smoke test failed: contract_validate not listed in tools.");
  }

  const call = await connection.sendRequest("tools/call", {
    name: "contract_validate",
    arguments: {}
  });
  const payload = call?.content?.[0];
  const ok =
    call &&
    call.isError === false &&
    payload?.type === "json" &&
    payload?.json?.ok === true;
  if (!ok) {
    throw new Error("Smoke test failed: tool call did not succeed.");
  }

  console.log("contract_validate smoke test passed.");
  completed = true;
  connection.dispose();
  if (!closed) {
    server.kill("SIGTERM");
  }
}

main().catch((error) => {
  console.error(error?.message || error);
  process.exit(1);
});
