#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./examples/audit-huggingface-clone.sh <huggingface-repo-url> [output-dir]

Clone a Hugging Face model repository into a temporary directory, run static
due diligence, write reports to the output directory and remove the clone.

Environment overrides (optional):
  MDD_TIMEOUT_SECONDS   Per-tool timeout (default: 300)
  MDD_FAIL_ON           Risk threshold: low|medium|high|critical (default: high)
  MDD_SKIP_EXTERNAL     Set to 1 or true to skip external scanners

Examples:
  ./examples/audit-huggingface-clone.sh \
    https://huggingface.co/Qwen/Qwen3-8B-GGUF \
    ./audit-qwen3
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 2
fi

repo_url="$1"
out_dir="${2:-${MDD_OUTPUT_DIR:-./model-audit-report}}"
timeout_seconds="${MDD_TIMEOUT_SECONDS:-300}"
fail_on="${MDD_FAIL_ON:-high}"
skip_external_flag=()

if [[ "${MDD_SKIP_EXTERNAL:-false}" == "1" || "${MDD_SKIP_EXTERNAL:-false}" == "true" ]]; then
  skip_external_flag=(--skip-external)
fi

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required but not found on PATH." >&2
  exit 127
fi

if ! command -v mdd >/dev/null 2>&1; then
  echo "ERROR: mdd is not installed. Run ./scripts/dev-setup.sh and activate .venv." >&2
  exit 127
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/mdd-hf-clone.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

echo "Cloning ${repo_url} into temporary directory."
git clone --depth 1 "$repo_url" "$tmpdir/clone"

echo "Running static due diligence."
mdd "$tmpdir/clone" \
  --out "$out_dir" \
  --timeout "$timeout_seconds" \
  --fail-on "$fail_on" \
  "${skip_external_flag[@]}"

echo "Reports written to: ${out_dir}"
