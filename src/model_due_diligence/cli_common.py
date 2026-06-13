"""Shared CLI argument definitions for scan commands."""

from __future__ import annotations

import argparse

from model_due_diligence.config.defaults import (
    DEFAULT_FAIL_ON,
    DEFAULT_OUTPUT_DIRECTORY,
    DEFAULT_TIMEOUT_SECONDS,
)
from model_due_diligence.domain.models import RiskLevel


def add_scan_options(parser: argparse.ArgumentParser) -> None:
    """Add scan, report and external-scanner options to an argument parser."""

    parser.add_argument(
        "--out",
        default=DEFAULT_OUTPUT_DIRECTORY,
        help=f"Output report directory. Default: {DEFAULT_OUTPUT_DIRECTORY}",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Per-tool timeout in seconds. Default: {DEFAULT_TIMEOUT_SECONDS}",
    )
    parser.add_argument(
        "--format",
        dest="formats",
        default="markdown,json,sarif",
        help="Comma-separated report formats to write: markdown,json,sarif. Default: markdown,json,sarif",
    )
    parser.add_argument("--skip-external", action="store_true", help="Skip all optional external scanner tools.")
    parser.add_argument("--skip-modelscan", action="store_true", help="Skip ModelScan.")
    parser.add_argument("--skip-semgrep", action="store_true", help="Skip Semgrep.")
    parser.add_argument("--skip-bandit", action="store_true", help="Skip Bandit.")
    parser.add_argument("--skip-pip-audit", action="store_true", help="Skip pip-audit.")
    parser.add_argument("--skip-detect-secrets", action="store_true", help="Skip detect-secrets.")
    parser.add_argument("--skip-quality-self-check", action="store_true", help="Skip project quality self-checks.")
    parser.add_argument(
        "--quality-self-check",
        action="store_true",
        help="Run Ruff, Pyright and mypy against this project as optional self-checks.",
    )
    parser.add_argument(
        "--fail-on",
        choices=[level.value.lower() for level in RiskLevel],
        default=DEFAULT_FAIL_ON.lower(),
        help=f"Return non-zero when risk is at or above this level. Default: {DEFAULT_FAIL_ON.lower()}",
    )
