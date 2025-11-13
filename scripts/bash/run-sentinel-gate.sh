#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: run-sentinel-gate.sh --gate <name> [--paths-json FILE] [--feature-dir PATH] [--repo-root PATH] [--decision ID]

Gates:
  constitution, specify, plan, tasks, clarify, analyze, checklist, implement
EOF
}

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    else
        echo "[sentinel-gate] Python is required to parse JSON paths." >&2
        exit 1
    fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GATE=""
PATHS_JSON=""
FEATURE_DIR=""
REPO_ROOT=""
DECISION_ID="${SENTINEL_DECISION:-D-SPECKIT}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --gate)
            shift
            GATE="${1:-}"
            ;;
        --paths-json)
            shift
            PATHS_JSON="${1:-}"
            ;;
        --feature-dir)
            shift
            FEATURE_DIR="${1:-}"
            ;;
        --repo-root)
            shift
            REPO_ROOT="${1:-}"
            ;;
        --decision)
            shift
            DECISION_ID="${1:-}"
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "[sentinel-gate] Unknown argument: $1" >&2
            usage
            exit 1
            ;;
    esac
    shift || true
done

if [[ -z "$GATE" ]]; then
    usage
    exit 1
fi

if [[ -n "$PATHS_JSON" && -f "$PATHS_JSON" ]]; then
    JSON_FEATURE_DIR=$("$PYTHON_BIN" <<'PY' "$PATHS_JSON"
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
try:
    data = json.loads(path.read_text())
except Exception:
    print("")
    sys.exit(0)
feature_dir = data.get("FEATURE_DIR")
spec_file = data.get("SPEC_FILE")
impl_plan = data.get("IMPL_PLAN")
if not feature_dir and spec_file:
    feature_dir = str(pathlib.Path(spec_file).parent)
if not feature_dir and impl_plan:
    feature_dir = str(pathlib.Path(impl_plan).parent)
print(feature_dir or "")
PY
)
    if [[ -z "$FEATURE_DIR" && -n "${JSON_FEATURE_DIR:-}" ]]; then
        FEATURE_DIR="$JSON_FEATURE_DIR"
    fi

    JSON_REPO_ROOT=$("$PYTHON_BIN" <<'PY' "$PATHS_JSON"
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
try:
    data = json.loads(path.read_text())
except Exception:
    print("")
    sys.exit(0)
print(data.get("REPO_ROOT") or "")
PY
)
    if [[ -z "$REPO_ROOT" && -n "${JSON_REPO_ROOT:-}" ]]; then
        REPO_ROOT="$JSON_REPO_ROOT"
    fi
fi

if [[ -z "$REPO_ROOT" ]]; then
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        REPO_ROOT="$(git rev-parse --show-toplevel)"
    else
        REPO_ROOT="$(pwd)"
    fi
fi

if [[ -z "$FEATURE_DIR" ]]; then
    FEATURE_DIR="$REPO_ROOT"
fi

if [[ ! -d "$REPO_ROOT" ]]; then
    echo "[sentinel-gate] Repo root '$REPO_ROOT' does not exist." >&2
    exit 1
fi

run_uv() {
    local description="$1"
    shift
    echo "[sentinel-gate] $description"
    if ! uv run sentinel --root "$REPO_ROOT" "$@"; then
        echo "[sentinel-gate] FAILED: $description" >&2
        exit 1
    fi
}

run_contracts() {
    run_uv "contracts validate" contracts validate
}

run_context() {
    run_uv "context lint" context lint
}

run_capsule() {
    if [[ ! -d "$FEATURE_DIR" ]]; then
        echo "[sentinel-gate] Skipping capsule check (feature directory missing: $FEATURE_DIR)"
        return
    fi
    run_uv "capsule generate (dry-run)" capsule generate "$FEATURE_DIR" --decision "$DECISION_ID" --agent "ROUTER" --dry-run
}

run_tests() {
    run_uv "sentinel tests" sentinels run
}

case "$GATE" in
    constitution)
        run_contracts
        run_context
        ;;
    specify)
        run_contracts
        run_context
        run_capsule
        ;;
    plan|tasks|clarify|analyze|checklist)
        run_contracts
        run_context
        ;;
    implement)
        run_contracts
        run_context
        run_capsule
        run_tests
        ;;
    *)
        echo "[sentinel-gate] Unknown gate '$GATE'." >&2
        exit 1
        ;;
esac

echo "[sentinel-gate] Gate '$GATE' completed successfully."
