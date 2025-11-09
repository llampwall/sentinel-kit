/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0013 */
import path from "node:path";
import fsp from "node:fs/promises";
import { fileURLToPath } from "node:url";
import Ajv from "ajv";
import addFormats from "ajv-formats";
import YAML from "yaml";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_ROOT = path.resolve(__dirname, "../../..");

function buildAjv(options = {}) {
  const ajv = new Ajv({ allErrors: true, strict: false, ...options });
  addFormats(ajv);
  return ajv;
}

/**
 * @param {object} [options]
 * @param {string} [options.root]
 * @param {string} [options.contractsDir]
 * @param {string} [options.fixturesDir]
 * @param {Ajv} [options.ajv]
 * @param {object} [options.ajvOptions]
 */
export function createContractValidator(options = {}) {
  const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
  const contractsDir = options.contractsDir || path.join(root, ".sentinel", "contracts");
  const fixturesDir = options.fixturesDir || path.join(contractsDir, "fixtures");
  const ajv = options.ajv || buildAjv(options.ajvOptions);
  const schemaCache = new Map();

  const isYaml = (file) => /\.ya?ml$/i.test(file);
  const isJson = (file) => /\.json$/i.test(file);

  async function loadSchemas(force = false) {
    if (!force && schemaCache.size) return schemaCache;
    schemaCache.clear();

    let files;
    try {
      files = await fsp.readdir(contractsDir);
    } catch (error) {
      throw new Error(
        `Unable to read contracts directory '${contractsDir}': ${error?.message || error}`
      );
    }

    for (const file of files) {
      if (!isYaml(file)) continue;
      const full = path.join(contractsDir, file);
      const raw = await fsp.readFile(full, "utf8");
      const parsed = YAML.parse(raw);
      const name = parsed?.contract || file.replace(/\.(ya?ml)$/i, "");
      const schema = parsed?.schema ?? parsed;
      try {
        schemaCache.set(name, {
          schema,
          validate: ajv.compile(schema),
          file: full
        });
      } catch (error) {
        throw new Error(`Failed to compile schema '${name}' (${full}): ${error?.message || error}`);
      }
    }

    return schemaCache;
  }

  async function* enumerateFixtures(filterContract = null) {
    let contractDirs;
    try {
      contractDirs = await fsp.readdir(fixturesDir, { withFileTypes: true });
    } catch {
      return;
    }

    for (const entry of contractDirs) {
      if (!entry.isDirectory()) continue;
      const contractName = entry.name;
      if (filterContract && contractName !== filterContract) continue;

      const contractPath = path.join(fixturesDir, contractName);
      let files;
      try {
        files = await fsp.readdir(contractPath);
      } catch {
        continue;
      }

      for (const file of files) {
        if (!isJson(file)) continue;
        yield {
          contractName,
          filePath: path.join(contractPath, file)
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
      if (first && typeof first.metadata?.ProducedBy === "string") return;
    } else if (typeof data === "object" && data !== null) {
      const header = data.metadata?.ProducedBy ?? data.ProducedBy;
      if (typeof header === "string") return;
    }

    throw new Error(
      `Fixture missing ProducedBy header: ${sourceFile}. Include ProducedBy=AGENT RulesHash=AGENT@X.Y Decision=D-####`
    );
  }

  async function validateFixture({ contract, fixture }) {
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

  async function validateAll({ contract = null } = {}) {
    await loadSchemas();
    const results = [];

    for await (const { contractName, filePath } of enumerateFixtures(contract)) {
      try {
        results.push(await validateFixture({ contract: contractName, fixture: filePath }));
      } catch (error) {
        results.push({
          ok: false,
          contract: contractName,
          fixture: filePath,
          errors: [error?.message ?? String(error)]
        });
      }
    }

    return {
      ok: results.every((result) => result.ok),
      results
    };
  }

  function clearCache() {
    schemaCache.clear();
  }

  return {
    root,
    contractsDir,
    fixturesDir,
    ajv,
    loadSchemas,
    clearCache,
    enumerateFixtures,
    loadFixture,
    ensureProducedByHeader,
    validateFixture,
    validateAll
  };
}

export const defaultValidator = createContractValidator();
export const { validateFixture, validateAll } = defaultValidator;

export default createContractValidator;
