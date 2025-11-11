import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Ajv, { type ValidateFunction } from "ajv";
import addFormats from "ajv-formats";
import YAML from "yaml";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_ROOT = path.resolve(__dirname, "../../..");
const DEFAULT_CONFIG = ".sentinel/context/limits/context-limits.json";
const DEFAULT_SCHEMA = ".sentinel/context/limits/context-limits.schema.json";

const ajv = addFormats(new Ajv({ allErrors: true, strict: false }));
let cachedSchemaPath: string | undefined;
let cachedValidator: ValidateFunction | undefined;

export interface ContextArtifactRule {
  name: string;
  globs: string[];
  maxLines?: number;
  enforceAllowedContext?: boolean;
}

export interface ContextOverrideRule {
  pattern: string;
  maxLines?: number;
  reason?: string;
}

export interface ContextLimitsConfig {
  defaultMaxLines: number;
  warningThreshold: number;
  forbiddenPaths: string[];
  artifacts: ContextArtifactRule[];
  overrides: ContextOverrideRule[];
}

export interface LoadContextLimitsOptions {
  root?: string;
  configPath?: string;
  schemaPath?: string;
}

interface RawContextLimits {
  defaultMaxLines: number;
  warningThreshold?: number;
  forbiddenPaths: string[];
  artifacts: ContextArtifactRule[];
  overrides?: ContextOverrideRule[];
}

export async function loadContextLimits(options: LoadContextLimitsOptions = {}): Promise<ContextLimitsConfig> {
  const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
  const configPath = path.resolve(root, options.configPath ?? DEFAULT_CONFIG);
  const schemaPath = path.resolve(root, options.schemaPath ?? DEFAULT_SCHEMA);
  const validator = await getValidator(schemaPath);
  const raw = await readConfig(configPath);
  if (!validator(raw)) {
    const message = ajv.errorsText(validator.errors, { separator: "\n" });
    throw new Error(`Context limit config failed schema validation (path=${relative(root, configPath)}):\n${message}`);
  }
  const normalized = normalizeConfig(raw as RawContextLimits);
  return normalized;
}

async function getValidator(schemaPath: string): Promise<ValidateFunction> {
  if (cachedValidator && cachedSchemaPath === schemaPath) {
    return cachedValidator;
  }
  const schemaRaw = await fs.readFile(schemaPath, "utf8");
  const schema = JSON.parse(schemaRaw);
  cachedSchemaPath = schemaPath;
  cachedValidator = ajv.compile(schema);
  return cachedValidator;
}

async function readConfig(configPath: string): Promise<unknown> {
  let raw: string;
  try {
    raw = await fs.readFile(configPath, "utf8");
  } catch (error) {
    throw new Error(`Unable to read context limit config '${configPath}': ${formatError(error)}`);
  }
  try {
    if (/\.(ya?ml)$/i.test(configPath)) {
      return YAML.parse(raw);
    }
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`Failed to parse context limit config '${configPath}': ${formatError(error)}`);
  }
}

function normalizeConfig(raw: RawContextLimits): ContextLimitsConfig {
  const warningThreshold = raw.warningThreshold ?? 0.9;
  if (warningThreshold <= 0 || warningThreshold > 1) {
    throw new Error(`warningThreshold must be between 0 and 1 (received ${warningThreshold})`);
  }
  return {
    defaultMaxLines: raw.defaultMaxLines,
    warningThreshold,
    forbiddenPaths: raw.forbiddenPaths.map(normalizePath),
    artifacts: raw.artifacts.map((artifact) => ({
      ...artifact,
      globs: artifact.globs.map(normalizePath)
    })),
    overrides: (raw.overrides ?? []).map((override) => ({
      ...override,
      pattern: normalizePath(override.pattern)
    }))
  };
}

function normalizePath(p: string): string {
  return p.replace(/\\/g, "/");
}

function relative(root: string, target: string): string {
  const rel = path.relative(root, target);
  return rel || path.basename(target);
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
