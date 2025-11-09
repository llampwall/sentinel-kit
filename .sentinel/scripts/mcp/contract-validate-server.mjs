#!/usr/bin/env node
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0014 */
/**
 * MCP server exposing the `contract_validate` tool over stdio.
 * Backed by the shared validator core used by the CLI.
 */

import path from "node:path";
import { fileURLToPath } from "node:url";
import watch from "node-watch";
import {
  StreamMessageReader,
  StreamMessageWriter
} from "vscode-jsonrpc/node.js";
import { createMessageConnection, ErrorCodes } from "vscode-jsonrpc";
import { createContractValidator } from "../contracts/validator-core.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../../..");
const WATCH_PATHS = [
  path.join(REPO_ROOT, ".sentinel", "contracts"),
  path.join(REPO_ROOT, ".sentinel", "contracts", "fixtures")
];

const validator = createContractValidator({ root: REPO_ROOT });

const reader = new StreamMessageReader(process.stdin);
const writer = new StreamMessageWriter(process.stdout);
const connection = createMessageConnection(reader, writer);

let cacheResetTimer = null;
function scheduleCacheReset() {
  clearTimeout(cacheResetTimer);
  cacheResetTimer = setTimeout(() => {
    validator.clearCache();
  }, 200);
}

for (const target of WATCH_PATHS) {
  try {
    watch(target, { recursive: true }, scheduleCacheReset);
  } catch {
    // Directory may not exist yet; ignore.
  }
}

async function runValidation({ contract, fixture }) {
  if (fixture) {
    const normalizedFixture = path.isAbsolute(fixture)
      ? fixture
      : path.resolve(REPO_ROOT, fixture);
    const inferredContract = contract || path.basename(path.dirname(normalizedFixture));
    const res = await validator.validateFixture({
      contract: inferredContract,
      fixture: normalizedFixture
    });
    return {
      ok: res.ok,
      results: [res]
    };
  }

  return validator.validateAll({ contract: contract || null });
}

connection.onRequest("initialize", () => ({
  protocolVersion: "2024-11-01",
  serverInfo: {
    name: "sentinel-contract-validate",
    version: "0.2.0"
  },
  capabilities: {
    tools: {
      listChanged: false
    }
  }
}));

connection.onRequest("tools/list", () => ({
  tools: [
    {
      name: "contract_validate",
      description:
        "Validate fixtures under .sentinel/contracts/fixtures/** against versioned contracts.",
      inputSchema: {
        type: "object",
        properties: {
          contract: {
            type: "string",
            description: "Optional contract name to scope validation (e.g., 'users.v1')."
          },
          fixture: {
            type: "string",
            description: "Optional path to a single fixture JSON file."
          }
        },
        additionalProperties: false
      }
    }
  ]
}));

connection.onRequest("tools/call", async (params = {}) => {
  if (params.name !== "contract_validate") {
    throw {
      code: ErrorCodes.MethodNotFound,
      message: `Unknown tool '${params.name}'`
    };
  }

  const args = params.arguments ?? {};
  try {
    const summary = await runValidation({
      contract: args.contract,
      fixture: args.fixture
    });
    return {
      content: [
        {
          type: "json",
          json: summary
        }
      ],
      isError: !summary.ok
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Validation failed: ${error?.message || error}`
        }
      ],
      isError: true
    };
  }
});

connection.onNotification("notifications/initialized", () => {});
connection.onRequest("ping", () => ({}));

connection.listen();

const shutdown = () => {
  try {
    connection.dispose();
  } finally {
    process.exit(0);
  }
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
