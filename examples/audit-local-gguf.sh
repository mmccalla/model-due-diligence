#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./examples/audit-local-gguf.sh <path-to-gguf-file> [output-dir]

Run static due diligence on a local GGUF (or other model) file.

Environment overrides (optional):
  MDD_TIMEOUT_SECONDS   Per-tool timeout (default: 300)
  MDD_FAIL_ON           Risk threshold: low|medium|high|critical (default: high)
  MDD_SKIP_EXTERNAL     Set to 1 or true to skip external scanners

Examples:
  ./examples/audit-local-gguf.sh ~/models/qwen3-8b-q4_k_m.gguf ./audit-qwen3-gguf
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

model_path="$1"
out_dir="${2:-${MDD_OUTPUT_DIR:-./model-audit-report}}"
timeout_seconds="${MDD_TIMEOUT_SECONDS:-300}"
fail_on="${MDD_FAIL_ON:-high}"
skip_external_flag=()

if [[ "${MDD_SKIP_EXTERNAL:-false}" == "1" || "${MDD_SKIP_EXTERNAL:-false}" == "true" ]]; then
  skip_external_flag=(--skip-external)
fi

if [[ ! -f "$model_path" ]]; then
  echo "ERROR: model file does not exist: ${model_path}" >&2
  exit 2
fi

if ! command -v mdd >/dev/null 2>&1; then
  echo "ERROR: mdd is not installed. Run ./scripts/dev-setup.sh and activate .venv." >&2
  exit 127
fi

echo "Scanning model file: ${model_path}"
mdd "$model_path" \
  --out "$out_dir" \
  --timeout "$timeout_seconds" \
  --fail-on "$fail_on" \
  "${skip_external_flag[@]}"

echo "Reports written to: ${out_dir}"
