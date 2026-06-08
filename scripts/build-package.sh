#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/build-package.sh [--skip-checks]

Build source and wheel distribution artefacts for model-due-diligence.

Options:
  --skip-checks    Skip quality gates before building.
  -h, --help       Show this help message.

Outputs:
  dist/*.tar.gz
  dist/*.whl
USAGE
}

skip_checks=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-checks)
      skip_checks=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "pyproject.toml" ]]; then
  echo "ERROR: run this script from the repository root." >&2
  exit 2
fi

python_cmd="${PYTHON:-python}"

if ! command -v "$python_cmd" >/dev/null 2>&1; then
  echo "ERROR: Python executable not found: $python_cmd" >&2
  exit 127
fi

if [[ "$skip_checks" == "false" ]]; then
  echo "Running quality gates before build."
  "$python_cmd" -m pip install --upgrade pip
  "$python_cmd" -m pip install -e ".[dev]"

  ruff format --check src tests
  ruff check src tests
  pyright
  mypy src tests
  pytest
else
  echo "Skipping quality gates."
fi

echo "Installing build dependencies."
"$python_cmd" -m pip install --upgrade pip
"$python_cmd" -m pip install build twine

echo "Cleaning previous distribution artefacts."
rm -rf dist/ build/ *.egg-info src/*.egg-info

echo "Building source and wheel distributions."
"$python_cmd" -m build

echo "Validating distribution metadata."
"$python_cmd" -m twine check dist/*

echo "Build complete."
ls -lh dist/
