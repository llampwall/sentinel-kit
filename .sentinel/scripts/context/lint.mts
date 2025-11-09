#!/usr/bin/env node
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import picomatch from "picomatch";
import {
  loadContextLimits,
  type ContextLimitsConfig,
  type ContextArtifactRule
} from "./config.mts";
import { extractListFromHeading } from "../lib/capsule-md.mjs";
import { normalizeInclude, assertIncludeExists } from "../lib/allowed-context.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_ROOT = path.resolve(__dirname, "../../..");

export interface LintArgs {
  root?: string;
  configPath?: string;
  schemaPath?: string;
  strict?: boolean;
  include?: string[];
}

export interface ContextLintIssue {
  file: string;
  message: string;
  severity: "error" | "warning";
  code: string;
}

export interface LintSummary {
  checkedFiles: number;
  issues: ContextLintIssue[];
  strict: boolean;
}

interface ArtifactFile {
  ruleName: string;
  relativePath: string;
  absolutePath: string;
  enforceAllowedContext: boolean;
  maxLines: number;
}

export async function lintContext(options: LintArgs = {}): Promise<LintSummary> {
  const root = options.root ? path.resolve(options.root) : DEFAULT_ROOT;
  const config = await loadContextLimits({ root, configPath: options.configPath, schemaPath: options.schemaPath });
  const includeSet = normalizeIncludeFilter(root, options.include);
  const files = await collectArtifactFiles(root, config, includeSet);
  const issues: ContextLintIssue[] = [];
  for (const file of files) {
    const content = await fs.readFile(file.absolutePath, "utf8");
    const lines = countLines(content);
    if (lines > file.maxLines) {
      issues.push({
        file: file.relativePath,
        code: "MAX_LINES",
        severity: "error",
        message: `exceeds ${file.maxLines} line budget (${lines} lines)`
      });
    } else if (lines / file.maxLines >= config.warningThreshold) {
      issues.push({
        file: file.relativePath,
        code: "NEAR_LIMIT",
        severity: "warning",
        message: `at ${(lines / file.maxLines * 100).toFixed(1)}% of limit (${lines}/${file.maxLines})`
      });
    }

    if (file.enforceAllowedContext) {
      const allowedEntries = extractListFromHeading(content, "Allowed Context");
      if (!allowedEntries.length) {
        issues.push({
          file: file.relativePath,
          code: "MISSING_ALLOWED_CONTEXT",
          severity: "error",
          message: "Allowed Context section is missing or empty"
        });
      } else {
        await validateAllowedContext({
          entries: allowedEntries,
          root,
          forbidden: config.forbiddenPaths,
          issues,
          file: file.relativePath
        });
      }
    }
  }

  return {
    checkedFiles: files.length,
    issues,
    strict: Boolean(options.strict)
  };
}

async function validateAllowedContext({
  entries,
  root,
  forbidden,
  issues,
  file
}: {
  entries: string[];
  root: string;
  forbidden: string[];
  issues: ContextLintIssue[];
  file: string;
}): Promise<void> {
  const seen = new Set<string>();
  for (const entry of entries) {
    let normalized: string;
    try {
      normalized = normalizeInclude(root, entry);
    } catch (error) {
      issues.push({
        file,
        code: "INVALID_INCLUDE",
        severity: "error",
        message: `${entry} -> ${formatError(error)}`
      });
      continue;
    }
    try {
      await assertIncludeExists(root, normalized);
    } catch (error) {
      issues.push({
        file,
        code: "MISSING_INCLUDE",
        severity: "error",
        message: `${normalized} -> ${formatError(error)}`
      });
      continue;
    }
    if (isForbidden(normalized, forbidden)) {
      issues.push({
        file,
        code: "FORBIDDEN_INCLUDE",
        severity: "error",
        message: `${normalized} is listed in forbiddenPaths`
      });
    }
    if (seen.has(normalized)) {
      issues.push({
        file,
        code: "DUPLICATE_INCLUDE",
        severity: "warning",
        message: `${normalized} is duplicated`
      });
    }
    seen.add(normalized);
  }
}

function isForbidden(entry: string, forbidden: string[]) {
  return forbidden.some((forbiddenPath) => entry === forbiddenPath || entry.startsWith(`${forbiddenPath}/`));
}

function normalizeIncludeFilter(root: string, include?: string[]): Set<string> | undefined {
  if (!include || !include.length) return undefined;
  const result = new Set<string>();
  for (const raw of include) {
    const abs = path.isAbsolute(raw) ? raw : path.resolve(root, raw);
    result.add(toPosix(path.relative(root, abs)));
  }
  return result;
}

async function collectArtifactFiles(
  root: string,
  config: ContextLimitsConfig,
  includeSet?: Set<string>
): Promise<ArtifactFile[]> {
  const files: ArtifactFile[] = [];
  const overrideMatchers = (config.overrides ?? []).map((override) => ({
    matcher: picomatch(override.pattern, { dot: true }),
    config: override
  }));

  for (const rule of config.artifacts) {
    for (const pattern of rule.globs) {
      const matcher = createMatcher(pattern);
      const matches = await resolvePatternMatches(root, matcher);
      for (const rel of matches) {
        if (includeSet && !includeSet.has(rel)) continue;
        const abs = path.resolve(root, rel);
        const limit = resolveMaxLines(rel, rule, config, overrideMatchers);
        files.push({
          ruleName: rule.name,
          relativePath: rel,
          absolutePath: abs,
          enforceAllowedContext: Boolean(rule.enforceAllowedContext),
          maxLines: limit
        });
      }
    }
  }
  return files;
}

function resolveMaxLines(
  file: string,
  rule: ContextArtifactRule,
  config: ContextLimitsConfig,
  overrides: { matcher: (input: string) => boolean; config: { maxLines?: number } }[]
): number {
  for (const override of overrides) {
    if (override.matcher(file) && override.config.maxLines) {
      return override.config.maxLines;
    }
  }
  return rule.maxLines ?? config.defaultMaxLines;
}

function createMatcher(pattern: string): {
  pattern: string;
  matcher: (input: string) => boolean;
  base: string;
  hasGlob: boolean;
} {
  const normalized = toPosix(pattern);
  const scan = picomatch.scan(normalized, { parts: false });
  return {
    pattern: normalized,
    matcher: picomatch(normalized, { dot: true }),
    base: scan.base && scan.base !== "." ? scan.base : ".",
    hasGlob: scan.isGlob
  };
}

async function resolvePatternMatches(
  root: string,
  matcher: { pattern: string; matcher: (input: string) => boolean; base: string; hasGlob: boolean }
): Promise<string[]> {
  if (!matcher.hasGlob) {
    const abs = path.resolve(root, matcher.pattern);
    try {
      const stats = await fs.stat(abs);
      if (stats.isFile()) {
        return [toPosix(path.relative(root, abs))];
      }
    } catch {
      return [];
    }
    return [];
  }
  const baseDir = path.resolve(root, matcher.base);
  const matches: string[] = [];
  await walkFiles(baseDir, async (absPath) => {
    const rel = toPosix(path.relative(root, absPath));
    if (matcher.matcher(rel)) {
      matches.push(rel);
    }
  });
  return matches;
}

async function walkFiles(dir: string, onFile: (absPath: string) => Promise<void>): Promise<void> {
  let dirents;
  try {
    dirents = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const entry of dirents) {
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walkFiles(abs, onFile);
    } else if (entry.isFile()) {
      await onFile(abs);
    }
  }
}

function countLines(content: string): number {
  if (!content) return 0;
  return content.split(/\r?\n/).length;
}

function toPosix(p: string): string {
  return p.replace(/\\/g, "/");
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function parseArgs(argv = process.argv.slice(2)): LintArgs {
  const args: LintArgs = { include: [] };
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    switch (token) {
      case "--config":
        args.configPath = requireValue(argv[++i], token);
        break;
      case "--schema":
        args.schemaPath = requireValue(argv[++i], token);
        break;
      case "--root":
        args.root = requireValue(argv[++i], token);
        break;
      case "--strict":
        args.strict = true;
        break;
      case "--capsule":
      case "--include":
        args.include?.push(requireValue(argv[++i], token));
        break;
      case "--help":
        printHelp();
        process.exit(0);
        break;
      default:
        throw new Error(`Unknown flag '${token}'`);
    }
  }
  if (args.include && args.include.length === 0) {
    delete args.include;
  }
  return args;
}

function requireValue(value: string | undefined, flag: string) {
  if (!value) throw new Error(`${flag} requires a value`);
  return value;
}

function printHelp() {
  console.log(`Usage: pnpm --dir=.sentinel context:lint [--strict] [--capsule <path>] [--config <path>]`);
}

async function cli(): Promise<void> {
  try {
    const args = parseArgs();
    const summary = await lintContext(args);
    if (!summary.issues.length) {
      console.log(`context:lint OK scanned ${summary.checkedFiles} file(s)`);
      return;
    }
    for (const issue of summary.issues) {
      const prefix = issue.severity === "error" ? "X" : "!";
      console.error(`${prefix} [${issue.code}] ${issue.file} -> ${issue.message}`);
    }
    const errors = summary.issues.filter((issue) => issue.severity === "error").length;
    const warnings = summary.issues.length - errors;
    console.error(`context:lint summary: ${errors} error(s), ${warnings} warning(s)`);
    const shouldFail = errors > 0 || (summary.strict && warnings > 0);
    if (shouldFail) {
      process.exit(1);
    }
  } catch (error) {
    console.error(`context:lint failed -> ${formatError(error)}`);
    process.exit(1);
  }
}


if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  cli();
}


