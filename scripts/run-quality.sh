
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/run-quality.sh [--fix] [--skip-types] [--skip-tests] [--skip-smoke]

Run local quality gates for model-due-diligence.

Options:
  --fix          Apply Ruff formatting and safe lint fixes before checks.
  --skip-types   Skip Pyright and mypy.
  --skip-tests   Skip pytest.
  --skip-smoke   Skip the CLI smoke test.
  -h, --help     Show this help message.

Default checks:
  - ruff format --check src tests
  - ruff check src tests
  - pyright
  - mypy src tests
  - pytest
  - mdd tests/fixtures/safe_repo --out ./audit-smoke --fail-on critical --skip-external
USAGE
}

fix=false
skip_types=false
skip_tests=false
skip_smoke=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fix)
      fix=true
      shift
      ;;
    --skip-types)
      skip_types=true
      shift
      ;;
    --skip-tests)
      skip_tests=true
      shift
      ;;
    --skip-smoke)
      skip_smoke=true
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

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "ERROR: required command not found on PATH: $command_name" >&2
    echo "Run ./scripts/dev-setup.sh, then activate the virtual environment with: source .venv/bin/activate" >&2
    exit 127
  fi
}

require_command ruff

if [[ "$skip_types" == "false" ]]; then
  require_command pyright
  require_command mypy
fi

if [[ "$skip_tests" == "false" ]]; then
  require_command pytest
fi

if [[ "$skip_smoke" == "false" ]]; then
  require_command mdd
fi

if [[ "$fix" == "true" ]]; then
  echo "Applying Ruff formatting and safe lint fixes."
  ruff format src tests
  ruff check src tests --fix
fi

echo "Checking Ruff formatting."
ruff format --check src tests

echo "Running Ruff lint checks."
ruff check src tests

if [[ "$skip_types" == "false" ]]; then
  echo "Running Pyright."
  pyright

  echo "Running mypy."
  mypy src tests
else
  echo "Skipping type checks."
fi

if [[ "$skip_tests" == "false" ]]; then
  echo "Running pytest."
  pytest
else
  echo "Skipping tests."
fi

if [[ "$skip_smoke" == "false" ]]; then
  echo "Running CLI smoke test."
  rm -rf ./audit-smoke
  mdd tests/fixtures/safe_repo \
    --out ./audit-smoke \
    --fail-on critical \
    --skip-external
else
  echo "Skipping CLI smoke test."
fi

echo "Quality gates completed successfully."
