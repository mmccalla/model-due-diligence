#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,scanners]"

#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/dev-setup.sh [--python <python-executable>] [--no-scanners] [--force]

Create or refresh a local development environment for model-due-diligence.

Options:
  --python <executable>  Python executable to use. Defaults to $PYTHON or python3.
  --no-scanners          Install only development dependencies, not optional scanner integrations.
  --force                Recreate the .venv directory if it already exists.
  -h, --help             Show this help message.

Examples:
  ./scripts/dev-setup.sh
  ./scripts/dev-setup.sh --python python3.12
  ./scripts/dev-setup.sh --no-scanners
  ./scripts/dev-setup.sh --force
USAGE
}

python_cmd="${PYTHON:-python3}"
install_scanners=true
force=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      if [[ -z "${2:-}" ]]; then
        echo "ERROR: --python requires a value." >&2
        exit 2
      fi
      python_cmd="$2"
      shift 2
      ;;
    --no-scanners)
      install_scanners=false
      shift
      ;;
    --force)
      force=true
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

if ! command -v "$python_cmd" >/dev/null 2>&1; then
  echo "ERROR: Python executable not found: $python_cmd" >&2
  exit 127
fi

if [[ "$force" == "true" && -d ".venv" ]]; then
  echo "Removing existing .venv directory."
  rm -rf .venv
fi

if [[ ! -d ".venv" ]]; then
  echo "Creating virtual environment with: $python_cmd"
  "$python_cmd" -m venv .venv
else
  echo "Using existing .venv directory."
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Python: $(python --version)"
echo "Pip: $(python -m pip --version)"

echo "Upgrading packaging tools."
python -m pip install --upgrade pip setuptools wheel

if [[ "$install_scanners" == "true" ]]; then
  echo "Installing package with development and scanner dependencies."
  python -m pip install -e ".[dev,scanners]"
else
  echo "Installing package with development dependencies only."
  python -m pip install -e ".[dev]"
fi

echo "Verifying CLI entry points."
python -m model_due_diligence --help >/dev/null
mdd --help >/dev/null
model-due-diligence --help >/dev/null

echo "Running lightweight quality smoke checks."
ruff --version
pyright --version
mypy --version
pytest --version

echo "Development environment ready."
echo "Activate it with: source .venv/bin/activate"
echo "Run quality gates with: ./scripts/run-quality.sh"
echo "Run tests with: ./scripts/run-tests.sh"