#!/usr/bin/env node
/* ProducedBy=SCRIBE RulesHash=DOCS@1.0 Decision=D-0003 */
/**
 * Minimal MCP server exposing the `contract.validate` tool.
 * Validates fixtures under .sentinel/contracts/fixtures/** against versioned contracts via JSON-RPC over stdio.
 */

import fs from "fs";
import fsp from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import YAML from "yaml";
import Ajv from "ajv";
import addFormats from "ajv-formats";

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);
const ROOT       = path.resolve(__dirname, "../../..");
const CONTRACTS  = path.join(ROOT, ".sentinel", "contracts");
const FIXTURES   = path.join(CONTRACTS, "fixtures");

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

// --------------------------- framing helpers ---------------------------
function send(msg) {
  const payload = JSON.stringify(msg);
  const header = `Content-Length: ${Buffer.byteLength(payload, "utf8")}\r\n\r\n`;
  process.stdout.write(header);
  process.stdout.write(payload);
}

let buffer = Buffer.alloc(0);
process.stdin.on("data", (chunk) => {
  buffer = Buffer.concat([buffer, chunk]);
  while (true) {
    const sep = buffer.indexOf("\r\n\r\n");
    if (sep === -1) break;
    const header = buffer.slice(0, sep).toString("utf8");
    const m = header.match(/Content-Length:\s*(\d+)/i);
    if (!m) { buffer = buffer.slice(sep + 4); continue; }
    const length = parseInt(m[1], 10);
    const start = sep + 4;
    if (buffer.length < start + length) break;
    const body = buffer.slice(start, start + length).toString("utf8");
    buffer = buffer.slice(start + length);
    try { handle(JSON.parse(body)); }
    catch (e) { /* ignore malformed */ }
  }
});

// --------------------------- tool impl ---------------------------
const isYaml = (f) => f.endsWith(".yaml") || f.endsWith(".yml");
const isJson = (f) => f.endsWith(".json");

async function loadContracts() {
  const map = new Map();
  let files = [];
  try { files = await fsp.readdir(CONTRACTS); } catch { return map; }
  for (const f of files) {
    if (!isYaml(f)) continue;
    const raw = await fsp.readFile(path.join(CONTRACTS, f), "utf8");
    const obj = YAML.parse(raw);
    const name = obj?.contract ?? f.replace(/\.(ya?ml)$/i, "");
    const schema = obj?.schema ?? obj;
    map.set(name, schema);
  }
  return map;
}

async function* enumerateFixtures(filterContract = null) {
  let domains = [];
  try {
    domains = await fsp.readdir(FIXTURES, { withFileTypes: true });
  } catch { return; }
  for (const d of domains) {
    if (!d.isDirectory()) continue;
    const contractName = d.name; // e.g. users.v1
    if (filterContract && filterContract !== contractName) continue;
    const dir = path.join(FIXTURES, contractName);
    const files = await fsp.readdir(dir);
    for (const f of files) {
      if (!isJson(f)) continue;
      yield { contractName, filePath: path.join(dir, f) };
    }
  }
}

async function validateAll({ contract, fixture }) {
  const contracts = await loadContracts();
  const results = [];
  const failures = [];

  if (fixture) {
    // Validate single fixture path
    const contractName = path.basename(path.dirname(fixture)); // .../fixtures/<name>/file.json
    const schema = contracts.get(contractName);
    if (!schema) {
      failures.push({ path: fixture, error: `No contract found for ${contractName}` });
    } else {
      const data = JSON.parse(await fsp.readFile(fixture, "utf8"));
      const validate = ajv.compile(schema);
      const ok = validate(data);
      if (!ok) failures.push({ path: fixture, error: ajv.errorsText(validate.errors, { separator: " | " }) });
      else results.push({ path: fixture, ok: true });
    }
  } else {
    // Validate every fixture (optionally filtered by contract name)
    for await (const { contractName, filePath } of enumerateFixtures(contract)) {
      const schema = contracts.get(contractName);
      if (!schema) {
        failures.push({ path: filePath, error: `No contract found for ${contractName}` });
        continue;
      }
      const data = JSON.parse(await fsp.readFile(filePath, "utf8"));
      const validate = ajv.compile(schema);
      const ok = validate(data);
      if (!ok) failures.push({ path: filePath, error: ajv.errorsText(validate.errors, { separator: " | " }) });
      else results.push({ path: filePath, ok: true });
    }
  }

  return { ok: failures.length === 0, results, failures };
}

// --------------------------- MCP handlers ---------------------------
function reply(id, result) { send({ jsonrpc: "2.0", id, result }); }
function error(id, code, message, data) { send({ jsonrpc: "2.0", id, error: { code, message, data } }); }

function handle(msg) {
  const { id, method, params } = msg || {};

  if (method === "initialize") {
    return reply(id, {
      protocolVersion: "2024-11-01",
      serverInfo: { name: "sentinel-contract-validate", version: "0.1.0" },
      capabilities: { tools: {} }
    });
  }

  if (method === "tools/list") {
    return reply(id, {
      tools: [{
        name: "contract.validate",
        description: "Validate fixtures under .sentinel/contracts/fixtures against versioned contracts.",
        inputSchema: {
          type: "object",
          properties: {
            contract: { type: "string", description: "Limit to a single contract name (e.g., 'users.v1')." },
            fixture:  { type: "string", description: "Validate a single fixture file path." }
          },
          additionalProperties: false
        }
      }]
    });
  }

  if (method === "tools/call") {
    const name = params?.name;
    const args = params?.arguments ?? {};
    if (name !== "contract.validate") return error(id, -32601, "Unknown tool");
    validateAll({ contract: args.contract, fixture: args.fixture })
      .then((res) => reply(id, { content: [{ type: "text", text: JSON.stringify(res, null, 2) }], isError: !res.ok }))
      .catch((e) => error(id, -32000, "Validation failed", String(e)));
    return;
  }

  // Required by MCP but we can noop most others.
  if (method === "notifications/initialized") return;
  if (method === "ping") return reply(id, {});

  // Fallback
  error(id, -32601, `Unknown method: ${method}`);
}

// Graceful shutdown
process.on("SIGINT", () => process.exit(0));
process.on("SIGTERM", () => process.exit(0));
