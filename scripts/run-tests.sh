#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/run-tests.sh [--unit] [--integration] [--coverage] [--smoke] [--all] [--pytest-args "<args>"]

Run tests for model-due-diligence.

Options:
  --unit                 Run unit tests only.
  --integration          Run integration tests only.
  --coverage             Run tests with coverage output.
  --smoke                Run the CLI smoke test after pytest.
  --all                  Run unit tests, integration tests and CLI smoke test. This is the default.
  --pytest-args "<args>" Pass additional arguments to pytest.
  -h, --help             Show this help message.

Examples:
  ./scripts/run-tests.sh
  ./scripts/run-tests.sh --unit
  ./scripts/run-tests.sh --coverage
  ./scripts/run-tests.sh --integration --pytest-args "-vv"
USAGE
}

run_unit=false
run_integration=false
run_smoke=false
coverage=false
pytest_args=()

if [[ $# -eq 0 ]]; then
  run_unit=true
  run_integration=true
  run_smoke=true
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --unit)
      run_unit=true
      shift
      ;;
    --integration)
      run_integration=true
      shift
      ;;
    --coverage)
      coverage=true
      shift
      ;;
    --smoke)
      run_smoke=true
      shift
      ;;
    --all)
      run_unit=true
      run_integration=true
      run_smoke=true
      shift
      ;;
    --pytest-args)
      if [[ -z "${2:-}" ]]; then
        echo "ERROR: --pytest-args requires a value." >&2
        exit 2
      fi
      # shellcheck disable=SC2206
      pytest_args=($2)
      shift 2
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

require_command pytest

if [[ "$run_smoke" == "true" ]]; then
  require_command mdd
fi

pytest_base=(pytest)

if [[ "$coverage" == "true" ]]; then
  pytest_base+=(--cov=src/model_due_diligence --cov-report=term-missing --cov-report=xml)
fi

if [[ "$run_unit" == "false" && "$run_integration" == "false" && "$run_smoke" == "false" ]]; then
  echo "ERROR: no test target selected." >&2
  usage >&2
  exit 2
fi

if [[ "$run_unit" == "true" ]]; then
  echo "Running unit tests."
  "${pytest_base[@]}" tests/unit "${pytest_args[@]}"
fi

if [[ "$run_integration" == "true" ]]; then
  echo "Running integration tests."
  "${pytest_base[@]}" tests/integration "${pytest_args[@]}"
fi

if [[ "$run_smoke" == "true" ]]; then
  echo "Running CLI smoke test."
  rm -rf ./audit-smoke
  mdd tests/fixtures/safe_repo \
    --out ./audit-smoke \
    --fail-on critical \
    --skip-external
fi

echo "Test run completed successfully."
