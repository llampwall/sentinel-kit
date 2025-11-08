/* ProducedBy=SCRIBE RulesHash=DOCS@1.0 Decision=D-0003 */
/**
 * CLI contract validator invoked via `npm run validate:contracts`.
 * Compiles every schema in .sentinel/contracts and validates each fixture under fixtures/.
 */

import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import YAML from "yaml";
import Ajv from "ajv";
import addFormats from "ajv-formats";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "../../");

const contractsDir = path.join(root, ".sentinel", "contracts");
const fixturesRoot = path.join(contractsDir, "fixtures");

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

const isYaml = (f) => f.endsWith(".yaml") || f.endsWith(".yml");
const isJson = (f) => f.endsWith(".json");

async function loadContracts() {
  const files = await fs.readdir(contractsDir);
  const map = new Map();
  for (const f of files) {
    if (!isYaml(f)) continue;
    const raw = await fs.readFile(path.join(contractsDir, f), "utf8");
    const obj = YAML.parse(raw);
    const name = obj?.contract ?? f.replace(/\.(ya?ml)$/i, "");
    const schema = obj?.schema ?? obj;
    map.set(name, schema);
  }
  return map;
}

async function* iterFixtures() {
  let entries = [];
  try {
    entries = await fs.readdir(fixturesRoot, { withFileTypes: true });
  } catch {
    return;
  }
  for (const dirent of entries) {
    if (!dirent.isDirectory()) continue;
    const contractName = dirent.name;           // e.g. users.v1
    const dir = path.join(fixturesRoot, contractName);
    const files = await fs.readdir(dir);
    for (const f of files) {
      if (!isJson(f)) continue;
      yield { contractName, filePath: path.join(dir, f) };
    }
  }
}

async function main() {
  const contracts = await loadContracts();
  const failures = [];

  for await (const { contractName, filePath } of iterFixtures()) {
    const schema = contracts.get(contractName);
    if (!schema) {
      failures.push({ filePath, error: `No contract found for ${contractName}` });
      continue;
    }
    const data = JSON.parse(await fs.readFile(filePath, "utf8"));
    const validate = ajv.compile(schema);
    const ok = validate(data);
    if (!ok) {
      failures.push({
        filePath,
        error: Ajv.errorsText ? Ajv.errorsText(validate.errors) : JSON.stringify(validate.errors)
      });
    }
  }

  if (failures.length) {
    console.error("❌ Contract validation failed:");
    for (const f of failures) console.error(`  - ${f.filePath}: ${f.error}`);
    process.exit(1);
  } else {
    console.log("✅ All fixtures validate against their contracts.");
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
