#!/usr/bin/env bash
# Install repository git hooks (commit-msg strips Cursor attribution trailers).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hooks_src="${repo_root}/.githooks"
hooks_dst="${repo_root}/.git/hooks"

if [[ ! -d "${repo_root}/.git" ]]; then
  echo "Not a git repository: ${repo_root}" >&2
  exit 1
fi

mkdir -p "${hooks_dst}"
install -m 755 "${hooks_src}/commit-msg" "${hooks_dst}/commit-msg"
echo "Installed ${hooks_dst}/commit-msg"
