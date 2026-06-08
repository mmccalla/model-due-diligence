#!/usr/bin/env bash
set -euo pipefail
ruff format --check src tests
ruff check src tests
pyright
mypy src tests
