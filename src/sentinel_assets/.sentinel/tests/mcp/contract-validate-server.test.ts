import { describe, it, expect, afterEach } from "vitest";
import path from "node:path";
import { spawn } from "node:child_process";
import {
  createMessageConnection,
  StreamMessageReader,
  StreamMessageWriter
} from "vscode-jsonrpc/node.js";

const SERVER = path.resolve("scripts", "mcp", "contract-validate-server.mjs");
const ROOT = path.resolve("..");

type RpcClient = {
  request: (method: string, params?: Record<string, unknown>) => Promise<unknown>;
  notify: (method: string, params?: Record<string, unknown>) => void;
  stop: () => Promise<void>;
};

function startServer(): RpcClient {
  const child = spawn(process.execPath, [SERVER], {
    cwd: ROOT,
    stdio: ["pipe", "pipe", "inherit"]
  });

  const connection = createMessageConnection(
    new StreamMessageReader(child.stdout),
    new StreamMessageWriter(child.stdin)
  );

  connection.listen();

  const stop = () =>
    new Promise((resolve) => {
      child.once("exit", () => resolve(undefined));
      child.kill("SIGTERM");
    });

  return {
    request: (method: string, params: Record<string, unknown> = {}) =>
      connection.sendRequest(method, params),
    notify: (method: string, params: Record<string, unknown> = {}) =>
      connection.sendNotification(method, params),
    stop: async () => {
      connection.dispose();
      await stop();
    }
  };
}

const servers: RpcClient[] = [];
afterEach(async () => {
  while (servers.length) {
    const server = servers.pop();
    if (server) {
      await server.stop();
    }
  }
});

describe("contract-validate MCP server", () => {
  it("lists the contract_validate tool", async () => {
    const server = startServer();
    servers.push(server);
    await server.request("initialize", {
      protocolVersion: "2024-11-01",
      capabilities: {},
      clientInfo: { name: "vitest", version: "0.0.0" }
    });
    server.notify("notifications/initialized");

    const list = (await server.request("tools/list", {})) as { tools?: Array<{ name: string }> };
    const names = list?.tools?.map((tool) => tool.name);
    expect(names).toContain("contract_validate");
  });

  it("validates all fixtures when no arguments are provided", async () => {
    const server = startServer();
    servers.push(server);
    await server.request("initialize", {
      protocolVersion: "2024-11-01",
      capabilities: {},
      clientInfo: { name: "vitest", version: "0.0.0" }
    });
    server.notify("notifications/initialized");
    await server.request("tools/list", {});

    const call = (await server.request("tools/call", {
      name: "contract_validate",
      arguments: {}
    })) as {
      content?: Array<{ type: string; json?: { ok?: boolean; results?: unknown[] } }>;
      isError?: boolean;
    };
    const payload = call?.content?.[0]?.json;
    expect(payload?.ok).toBe(true);
    expect(Array.isArray(payload?.results)).toBe(true);
  });

  it("returns an error payload when validation fails", async () => {
    const server = startServer();
    servers.push(server);
    await server.request("initialize", {
      protocolVersion: "2024-11-01",
      capabilities: {},
      clientInfo: { name: "vitest", version: "0.0.0" }
    });
    server.notify("notifications/initialized");
    await server.request("tools/list", {});

    const call = (await server.request("tools/call", {
      name: "contract_validate",
      arguments: { fixture: "does-not-exist.json" }
    })) as { isError?: boolean };
    expect(call?.isError).toBe(true);
  });
});
