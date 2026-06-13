#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./examples/audit-installed-ollama.sh <ollama-model-name> [output-dir]

Resolve an installed Ollama model from the local store and run static due
diligence on its staged artefacts. The Ollama server does not need to be running.

Environment overrides (optional):
  MDD_TIMEOUT_SECONDS   Per-tool timeout (default: 300)
  MDD_FAIL_ON           Risk threshold: low|medium|high|critical (default: high)
  MDD_SKIP_EXTERNAL     Set to 1 or true to skip external scanners

Examples:
  ./examples/audit-installed-ollama.sh qwen3:4b ./audit-qwen3-ollama
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

model_name="$1"
out_dir="${2:-${MDD_OUTPUT_DIR:-./model-audit-report}}"
timeout_seconds="${MDD_TIMEOUT_SECONDS:-300}"
fail_on="${MDD_FAIL_ON:-high}"
skip_external_flag=()

if [[ "${MDD_SKIP_EXTERNAL:-false}" == "1" || "${MDD_SKIP_EXTERNAL:-false}" == "true" ]]; then
  skip_external_flag=(--skip-external)
fi

if ! command -v mdd-ollama >/dev/null 2>&1; then
  echo "ERROR: mdd-ollama is not installed. Run ./scripts/dev-setup.sh and activate .venv." >&2
  exit 127
fi

echo "Scanning installed Ollama model: ${model_name}"
mdd-ollama "$model_name" \
  --out "$out_dir" \
  --timeout "$timeout_seconds" \
  --fail-on "$fail_on" \
  "${skip_external_flag[@]}"

echo "Reports written to: ${out_dir}"
