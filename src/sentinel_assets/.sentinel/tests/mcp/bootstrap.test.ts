import { describe, it, expect, afterEach } from "vitest";
import { PassThrough } from "node:stream";
import {
  createMessageConnection,
  StreamMessageReader,
  StreamMessageWriter
} from "vscode-jsonrpc/node.js";
import { z } from "zod";
import { createMcpServer } from "../../scripts/mcp/lib/bootstrap.mjs";

type ToolContent =
  | { type: "text"; text: string }
  | { type: "json"; json: unknown };

type ToolDefinition = {
  name: string;
  description?: string;
  schema?: z.ZodTypeAny;
  handler: (args: unknown) => Promise<{ ok: boolean; content?: ToolContent[] }>;
};

type ToolListResponse = {
  tools: Array<{ name: string; inputSchema: Record<string, unknown> }>;
};

type ToolCallResponse = {
  isError?: boolean;
  content: ToolContent[];
};

function createInMemoryServer(tool: ToolDefinition) {
  const clientToServer = new PassThrough();
  const serverToClient = new PassThrough();

  const server = createMcpServer({
    name: "test",
    version: "0.0.0",
    reader: new StreamMessageReader(clientToServer),
    writer: new StreamMessageWriter(serverToClient),
    tools: [tool]
  });

  const clientConnection = createMessageConnection(
    new StreamMessageReader(serverToClient),
    new StreamMessageWriter(clientToServer)
  );
  clientConnection.listen();

  return { server, clientConnection };
}

const clients: Array<{ connection: ReturnType<typeof createMessageConnection> }> = [];
afterEach(() => {
  while (clients.length) {
    const entry = clients.pop();
    entry?.connection?.dispose();
  }
});

describe("mcp bootstrap", () => {
  it("lists registered tools with generated json schema", async () => {
    const { clientConnection } = createInMemoryServer({
      name: "echo",
      description: "Echo input",
      schema: z.object({ text: z.string() }),
      handler: async (args) => ({
        ok: true,
        content: [{ type: "text", text: (args as { text: string }).text }]
      })
    });
    clients.push({ connection: clientConnection });

    await clientConnection.sendRequest("initialize", {
      protocolVersion: "2024-11-01",
      capabilities: {},
      clientInfo: { name: "test", version: "0.0.0" }
    });
    const list = (await clientConnection.sendRequest("tools/list", {})) as ToolListResponse;
    expect(list.tools).toHaveLength(1);
    expect(list.tools[0].name).toBe("echo");
    const schema = list.tools[0].inputSchema;
    expect(schema).toHaveProperty("definitions.echoInput.properties.text.type", "string");
  });

  it("validates tool arguments via zod schema", async () => {
    const { clientConnection } = createInMemoryServer({
      name: "sum",
      description: "Adds values",
      schema: z.object({ values: z.array(z.number()).min(1) }),
      handler: async (args) => {
        const payload = args as { values: number[] };
        return {
          ok: true,
          content: [
            {
              type: "json",
              json: { total: payload.values.reduce((acc, value) => acc + value, 0) }
            }
          ]
        };
      }
    });
    clients.push({ connection: clientConnection });

    await clientConnection.sendRequest("initialize", {
      protocolVersion: "2024-11-01",
      capabilities: {},
      clientInfo: { name: "test", version: "0.0.0" }
    });

    await expect(
      clientConnection.sendRequest("tools/call", { name: "sum", arguments: {} })
    ).rejects.toThrow();
  });

  it("returns normalized error responses when handler throws", async () => {
    const { clientConnection } = createInMemoryServer({
      name: "fail",
      description: "Failing tool",
      schema: z.object({}),
      handler: async () => {
        throw new Error("boom");
      }
    });
    clients.push({ connection: clientConnection });

    await clientConnection.sendRequest("initialize", {
      protocolVersion: "2024-11-01",
      capabilities: {},
      clientInfo: { name: "test", version: "0.0.0" }
    });

    const response = (await clientConnection.sendRequest("tools/call", {
      name: "fail",
      arguments: {}
    })) as ToolCallResponse;
    expect(response.isError).toBe(true);
    expect(response.content[0].type).toBe("text");
  });
});


