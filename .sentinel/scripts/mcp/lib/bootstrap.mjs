/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0015 */
import { StreamMessageReader, StreamMessageWriter } from "vscode-jsonrpc/node.js";
import { createMessageConnection, ErrorCodes } from "vscode-jsonrpc";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";

const DEFAULT_PROTOCOL_VERSION = "2024-11-01";
const DEFAULT_SERVER_INFO = {
  name: "sentinel-mcp-server",
  version: "0.0.0"
};

const TOOL_RESPONSE_SCHEMA = z.object({
  ok: z.boolean().default(true),
  content: z
    .array(
      z.union([
        z.object({ type: z.literal("text"), text: z.string() }),
        z.object({ type: z.literal("json"), json: z.any() })
      ])
    )
    .optional()
});

function toJsonSchema(schema, name) {
  try {
    return zodToJsonSchema(schema, name || "Input");
  } catch {
    return { type: "object", additionalProperties: true };
  }
}

function normalizeResponse(payload) {
  const parsed = TOOL_RESPONSE_SCHEMA.safeParse(payload);
  if (!parsed.success) {
    return {
      content: [
        {
          type: "text",
          text: "Tool handler returned an invalid response"
        }
      ],
      isError: true
    };
  }

  if (parsed.data.content && parsed.data.content.length > 0) {
    return {
      content: parsed.data.content,
      isError: parsed.data.ok === false
    };
  }

  return {
    content: [
      {
        type: "json",
        json: { ok: parsed.data.ok }
      }
    ],
    isError: parsed.data.ok === false
  };
}

/**
 * @param {object} options
 * @param {string} options.name
 * @param {string} options.version
 * @param {import("zod").ZodTypeAny} [options.defaultInputSchema]
 * @param {Array<{ name: string; description?: string; schema?: import("zod").ZodTypeAny; handler: (args: any) => Promise<any>; }>} options.tools
 * @param {StreamMessageReader} [options.reader]
 * @param {StreamMessageWriter} [options.writer]
 * @param {string} [options.protocolVersion]
 */
export function createMcpServer({
  name = DEFAULT_SERVER_INFO.name,
  version = DEFAULT_SERVER_INFO.version,
  tools = [],
  reader = new StreamMessageReader(process.stdin),
  writer = new StreamMessageWriter(process.stdout),
  protocolVersion = DEFAULT_PROTOCOL_VERSION,
  defaultInputSchema = z.object({}).passthrough()
}) {
  const connection = createMessageConnection(reader, writer);
  const toolMap = new Map();

  for (const tool of tools) {
    if (!tool?.name) {
      throw new Error("Tool definition requires a name");
    }
    if (toolMap.has(tool.name)) {
      throw new Error(`Duplicate tool name '${tool.name}'`);
    }
    const schema = tool.schema || defaultInputSchema;
    toolMap.set(tool.name, {
      name: tool.name,
      description: tool.description || "",
      schema,
      schemaJson: toJsonSchema(schema, `${tool.name}Input`),
      handler: tool.handler
    });
  }

  connection.onRequest("initialize", () => ({
    protocolVersion,
    serverInfo: { name, version },
    capabilities: { tools: { listChanged: false } }
  }));

  connection.onRequest("tools/list", () => ({
    tools: Array.from(toolMap.values()).map((tool) => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.schemaJson
    }))
  }));

  connection.onRequest("tools/call", async (params = {}) => {
    const tool = toolMap.get(params.name);
    if (!tool) {
      const error = new Error(`Unknown tool '${params.name}'`);
      error.code = ErrorCodes.MethodNotFound;
      throw error;
    }
    let parsedArgs;
    try {
      parsedArgs = tool.schema.parse(params.arguments ?? {});
    } catch (error) {
      const message = Array.isArray(error?.errors)
        ? error.errors.map((entry) => entry.message).join("; ")
        : error?.message || "Invalid arguments";
      const invalid = new Error(message);
      invalid.code = ErrorCodes.InvalidParams;
      throw invalid;
    }
    try {
      const response = await tool.handler(parsedArgs);
      return normalizeResponse(response);
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: error?.message || "Tool handler failed"
          }
        ],
        isError: true
      };
    }
  });

  connection.onNotification("notifications/initialized", () => {});
  connection.onRequest("ping", () => ({}));
  connection.listen();

  return {
    connection,
    dispose: () => connection.dispose()
  };
}

export default {
  createMcpServer
};

