#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./examples/audit-installed-ollama.sh <ollama-model-name> [output-dir]

Example:
  ./examples/audit-installed-ollama.sh qwen3:4b ./audit-qwen3-ollama

Notes:
  - The scan resolves an installed Ollama model from the local manifest/blob store.
  - A temporary staging directory is created so the scanner can inspect friendly filenames.
  - The model is not loaded or executed by this script.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

model_name="$1"
out_dir="${2:-./audit-ollama}"

if ! command -v mdd-ollama >/dev/null 2>&1; then
  echo "ERROR: mdd-ollama is not installed or not available on PATH." >&2
  echo "Install the project first, for example: python -m pip install -e '.[dev,scanners]'" >&2
  exit 127
fi

echo "Scanning installed Ollama model."
echo "Model name: $model_name"
echo "Output directory: $out_dir"

mdd-ollama "$model_name" \
  --out "$out_dir" \
  --fail-on high

echo "Audit complete."
echo "Markdown report: $out_dir/model_due_diligence_report.md"
echo "JSON report: $out_dir/model_due_diligence_report.json"
