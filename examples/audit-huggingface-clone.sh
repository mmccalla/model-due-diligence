
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./examples/audit-huggingface-clone.sh <hugging-face-repo-url> [output-dir]

Example:
  ./examples/audit-huggingface-clone.sh https://huggingface.co/Qwen/Qwen3-8B-GGUF ./audit-qwen3

Notes:
  - The repository is cloned into a temporary directory.
  - The scan runs against the cloned repository.
  - The generated audit report is written to the output directory.
  - No model files are loaded or executed by this script.
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

repo_url="$1"
out_dir="${2:-./audit-hf}"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed or not available on PATH." >&2
  exit 127
fi

if ! command -v mdd >/dev/null 2>&1; then
  echo "ERROR: mdd is not installed or not available on PATH." >&2
  echo "Install the project first, for example: python -m pip install -e '.[dev,scanners]'" >&2
  exit 127
fi

work_dir="$(mktemp -d -t model-due-diligence-hf.XXXXXX)"
cleanup() {
  rm -rf "$work_dir"
}
trap cleanup EXIT

clone_dir="$work_dir/model-under-test"

echo "Cloning Hugging Face repository: $repo_url"
git clone --depth 1 "$repo_url" "$clone_dir"

echo "Scanning cloned repository."
echo "Clone directory: $clone_dir"
echo "Output directory: $out_dir"

mdd "$clone_dir" \
  --out "$out_dir" \
  --fail-on high

echo "Audit complete."
echo "Markdown report: $out_dir/model_due_diligence_report.md"
echo "JSON report: $out_dir/model_due_diligence_report.json"
