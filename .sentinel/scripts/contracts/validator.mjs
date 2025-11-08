import path from "path";
import fsp from "fs/promises";
import YAML from "yaml";
import Ajv from "ajv";
import addFormats from "ajv-formats";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../../..");
const CONTRACTS_DIR = path.join(ROOT, ".sentinel", "contracts");
const FIXTURES_DIR = path.join(CONTRACTS_DIR, "fixtures");

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

const schemaCache = new Map();

const isYaml = (file) => /\.ya?ml$/i.test(file);
const isJson = (file) => /\.json$/i.test(file);

async function loadSchemas() {
  if (schemaCache.size) return schemaCache;

  const files = await fsp.readdir(CONTRACTS_DIR);
  for (const file of files) {
    if (!isYaml(file)) continue;
    const full = path.join(CONTRACTS_DIR, file);
    const raw = await fsp.readFile(full, "utf8");
    const parsed = YAML.parse(raw);
    const name = parsed?.contract ?? file.replace(/\.(ya?ml)$/i, "");
    const schema = parsed?.schema ?? parsed;
    schemaCache.set(name, {
      schema,
      validate: ajv.compile(schema),
      file: full
    });
  }
  return schemaCache;
}

async function* enumerateFixtures(filterContract = null) {
  let dirs = [];
  try {
    dirs = await fsp.readdir(FIXTURES_DIR, { withFileTypes: true });
  } catch {
    return;
  }

  for (const dir of dirs) {
    if (!dir.isDirectory()) continue;
    const contractName = dir.name;
    if (filterContract && contractName !== filterContract) continue;

    const dirPath = path.join(FIXTURES_DIR, contractName);
    const files = await fsp.readdir(dirPath);
    for (const file of files) {
      if (!isJson(file)) continue;
      yield {
        contractName,
        filePath: path.join(dirPath, file)
      };
    }
  }
}

async function loadFixture(filePath) {
  const content = await fsp.readFile(filePath, "utf8");
  return JSON.parse(content);
}

function ensureProducedByHeader(data, sourceFile) {
  if (Array.isArray(data)) {
    const first = data[0];
    if (first && typeof first.ProducedBy === "string") return;
  } else if (typeof data === "object" && data !== null) {
    const header = data.metadata?.ProducedBy ?? data.ProducedBy;
    if (typeof header === "string") return;
  }

  throw new Error(
    `Fixture missing ProducedBy header: ${sourceFile}. Include ProducedBy=AGENT RulesHash=AGENT@X.Y Decision=D-####`
  );
}

export async function validateFixture({ contract, fixture }) {
  const schemas = await loadSchemas();
  if (!schemas.has(contract)) {
    throw new Error(`No contract schema named '${contract}'.`);
  }

  const record = schemas.get(contract);
  const payload = await loadFixture(fixture);
  ensureProducedByHeader(payload, fixture);
  const ok = record.validate(payload);

  return {
    ok,
    contract,
    fixture,
    errors: ok ? [] : record.validate.errors ?? []
  };
}

export async function validateAll({ contract = null } = {}) {
  const schemas = await loadSchemas();
  const results = [];

  for await (const { contractName, filePath } of enumerateFixtures(contract)) {
    if (!schemas.has(contractName)) {
      results.push({
        ok: false,
        contract: contractName,
        fixture: filePath,
        errors: [`No contract schema found for '${contractName}'`]
      });
      continue;
    }

    try {
      results.push(await validateFixture({ contract: contractName, fixture: filePath }));
    } catch (err) {
      results.push({
        ok: false,
        contract: contractName,
        fixture: filePath,
        errors: [err?.message ?? String(err)]
      });
    }
  }

  return {
    ok: results.every((r) => r.ok),
    results
  };
}

