#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./examples/audit-local-gguf.sh <path-to-gguf-file> [output-dir]

Example:
  ./examples/audit-local-gguf.sh ~/models/qwen3-8b-q4_k_m.gguf ./audit-qwen3-gguf

Notes:
  - The scan runs against a local GGUF file.
  - The generated audit report is written to the output directory.
  - The model file is not loaded or executed by this script.
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

model_file="$1"
out_dir="${2:-./audit-gguf}"

if ! command -v mdd >/dev/null 2>&1; then
  echo "ERROR: mdd is not installed or not available on PATH." >&2
  echo "Install the project first, for example: python -m pip install -e '.[dev,scanners]'" >&2
  exit 127
fi

if [[ ! -f "$model_file" ]]; then
  echo "ERROR: model file does not exist or is not a regular file: $model_file" >&2
  exit 2
fi

case "${model_file,,}" in
  *.gguf)
    ;;
  *)
    echo "ERROR: expected a .gguf file: $model_file" >&2
    exit 2
    ;;
esac

echo "Scanning local GGUF file."
echo "Model file: $model_file"
echo "Output directory: $out_dir"

mdd "$model_file" \
  --out "$out_dir" \
  --fail-on high

echo "Audit complete."
echo "Markdown report: $out_dir/model_due_diligence_report.md"
echo "JSON report: $out_dir/model_due_diligence_report.json"
