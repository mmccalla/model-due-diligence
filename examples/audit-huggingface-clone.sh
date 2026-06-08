#!/usr/bin/env bash
set -euo pipefail
git clone "$1" model-under-test
mdd ./model-under-test --out ./audit-hf
