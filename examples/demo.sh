#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./examples/demo.sh [output-dir]

Run the bundled suspicious-repo demo used in the README and launch posts.
No network access or external scanner CLIs are required.

Examples:
  ./examples/demo.sh
  ./examples/demo.sh ./audit-demo
USAGE
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out_dir="${1:-${MDD_OUTPUT_DIR:-./audit-demo}}"
timeout_seconds="${MDD_TIMEOUT_SECONDS:-300}"
fail_on="${MDD_FAIL_ON:-critical}"

if ! command -v mdd >/dev/null 2>&1; then
  if [[ -x "${repo_root}/.venv/bin/mdd" ]]; then
    export PATH="${repo_root}/.venv/bin:${PATH}"
  else
    echo "ERROR: mdd is not installed. Run ./scripts/dev-setup.sh and activate .venv." >&2
    exit 127
  fi
fi

target="${repo_root}/tests/fixtures/suspicious_repo"
if [[ ! -d "$target" ]]; then
  echo "ERROR: demo fixture not found at ${target}" >&2
  echo "Run this script from a cloned repository checkout." >&2
  exit 2
fi

echo "Running demo scan against bundled suspicious fixture."
mdd "$target" \
  --out "$out_dir" \
  --timeout "$timeout_seconds" \
  --fail-on "$fail_on" \
  --skip-external

echo
echo "Demo complete."
echo "Risk summary:"
grep -E '^\*\*Risk level:\*\*|^\*\*Risk score:\*\*' "${out_dir}/model_due_diligence_report.md" || true
echo
echo "Full report: ${out_dir}/model_due_diligence_report.md"
