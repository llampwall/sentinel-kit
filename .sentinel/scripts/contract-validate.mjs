#!/usr/bin/env node
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0013 */
import path from "path";
import { fileURLToPath } from "url";
import watch from "node-watch";
import { validateAll, validateFixture } from "./contracts/validator.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SENTINEL_ROOT = path.resolve(__dirname, "..");
const REPO_ROOT = path.resolve(SENTINEL_ROOT, "..");
const WATCH_PATHS = [
  path.join(REPO_ROOT, ".sentinel", "contracts"),
  path.join(REPO_ROOT, ".sentinel", "contracts", "fixtures")
];

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    contract: null,
    fixture: null,
    watch: false
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === "--contract" || arg === "-c") {
      options.contract = args[i + 1];
      i += 1;
    } else if (arg === "--fixture" || arg === "-f") {
      options.fixture = args[i + 1];
      i += 1;
    } else if (arg === "--watch" || arg === "-w") {
      options.watch = true;
    }
  }

  return options;
}

function printResult(result) {
  console.log(JSON.stringify(result, null, 2));
}

async function runValidationOnce(options) {
  const { contract, fixture } = options;
  if (contract && fixture) {
    const res = await validateFixture({ contract, fixture });
    return {
      ok: res.ok,
      results: [res]
    };
  }

  if (fixture) {
    const inferredContract = path.basename(path.dirname(fixture));
    const res = await validateFixture({ contract: inferredContract, fixture });
    return {
      ok: res.ok,
      results: [res]
    };
  }

  return validateAll({ contract });
}

async function runAndReport(options) {
  try {
    const result = await runValidationOnce(options);
    printResult(result);
    process.exitCode = result.ok ? 0 : 1;
  } catch (err) {
    const payload = {
      ok: false,
      error: err?.message ?? String(err)
    };
    printResult(payload);
    process.exitCode = 1;
  }
}

function watchForChanges(options) {
  console.log("👀 Watching .sentinel/contracts/** for changes...");
  let timer = null;
  const scheduleRun = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      runAndReport(options);
    }, 200);
  };

  watch(WATCH_PATHS, { recursive: true }, (event, filename) => {
    console.log(`[watch] ${event} -> ${filename}`);
    scheduleRun();
  });
}

async function main() {
  const options = parseArgs();
  await runAndReport(options);

  if (options.watch) {
    watchForChanges(options);
  } else if (process.exitCode !== 0) {
    process.exit(process.exitCode);
  }
}

main();
