#!/usr/bin/env node
/**
 * Smoke test for the contract_validate MCP server. Spins up the server,
 * performs initialize -> tools/list -> tools/call, and exits non-zero if
 * any step fails.
 */

import { spawn } from "node:child_process";

const server = spawn(process.execPath, [".sentinel/scripts/mcp/contract-validate-server.mjs"], {
  stdio: ["pipe", "pipe", "inherit"]
});

let buffer = "";
let awaitingToolResponse = true;

server.stdin.setDefaultEncoding("utf8");
server.stdout.setEncoding("utf8");

server.stdout.on("data", (chunk) => {
  buffer += chunk;
  while (true) {
    const nl = buffer.indexOf("\n");
    if (nl === -1) break;
    const line = buffer.slice(0, nl).trim();
    buffer = buffer.slice(nl + 1);
    if (!line) continue;
    handleMessage(line);
  }
});

server.on("exit", (code) => {
  if (code !== 0 && awaitingToolResponse) {
    console.error("Smoke test failed: server exited before completing tool call.");
    process.exit(1);
  }
});

function send(msg) {
  server.stdin.write(JSON.stringify(msg) + "\n");
}

function handleMessage(line) {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch (err) {
    console.error("Smoke test received invalid JSON:", line);
    process.exit(1);
  }

  if (msg.id === 1) {
    // initialization succeeded
    send({ jsonrpc: "2.0", method: "notifications/initialized" });
    send({ jsonrpc: "2.0", id: 2, method: "tools/list" });
    return;
  }

  if (msg.id === 2) {
    const toolNames = msg.result?.tools?.map((t) => t.name) ?? [];
    if (!toolNames.includes("contract_validate")) {
      console.error("Smoke test failed: contract_validate not listed in tools.");
      process.exit(1);
    }
    send({ jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "contract_validate", arguments: {} } });
    return;
  }

  if (msg.id === 3) {
    awaitingToolResponse = false;
    const ok = msg.result && msg.result.isError === false;
    if (!ok) {
      console.error("Smoke test failed: tool call did not succeed.", msg);
      process.exit(1);
    }
    console.log("contract_validate smoke test passed.");
    server.kill("SIGTERM");
    return;
  }
}

// Kick off initialize
send({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-01",
    capabilities: {},
    clientInfo: { name: "smoke-client", version: "0.0.0" }
  }
});

// Safety timeout
setTimeout(() => {
  if (awaitingToolResponse) {
    console.error("Smoke test timed out.");
    server.kill("SIGTERM");
    process.exit(1);
  }
}, 5000);
