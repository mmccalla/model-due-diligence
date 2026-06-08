"""Command-line interface for model-due-diligence.

The CLI owns argument parsing, context construction, report writing and process
exit behaviour. Scanning orchestration belongs in `app.py`; scanner-specific
logic belongs in scanner modules.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from model_due_diligence.app import ModelDueDiligenceApp
from model_due_diligence.config.defaults import (
    APP_NAME,
    DEFAULT_FAIL_ON,
    DEFAULT_OUTPUT_DIRECTORY,
    DEFAULT_TIMEOUT_SECONDS,
)
from model_due_diligence.domain.models import AuditReport, ReportFormat, RiskLevel, ScanContext
from model_due_diligence.reporting.json_report import write_json_report_to_directory
from model_due_diligence.reporting.markdown_report import write_markdown_report_to_directory
from model_due_diligence.reporting.sarif_report import write_sarif_report_to_directory

RISK_LEVEL_ORDER: dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Static due-diligence scanner for local AI model artefacts and repositories.",
    )

    parser.add_argument("target", help="Path to a model file or model directory.")
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
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} 0.1.0",
    )

    return parser.parse_args(argv)


def build_context(args: argparse.Namespace) -> ScanContext:
    """Build the immutable scan context from parsed CLI arguments."""

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target does not exist: {target}")

    output_dir = Path(args.out).expanduser().resolve()
    root = target if target.is_dir() else target.parent

    return ScanContext(
        target=target,
        root=root,
        output_dir=output_dir,
        timeout_seconds=args.timeout,
        fail_on=RiskLevel(args.fail_on.upper()),
        report_formats=parse_report_formats(args.formats),
        skip_external=args.skip_external,
        skip_semgrep=args.skip_semgrep,
        skip_bandit=args.skip_bandit,
        skip_pip_audit=args.skip_pip_audit,
        skip_detect_secrets=args.skip_detect_secrets,
        skip_modelscan=args.skip_modelscan,
        skip_quality_self_check=args.skip_quality_self_check,
        quality_self_check=args.quality_self_check,
    )


def parse_report_formats(value: str) -> tuple[ReportFormat, ...]:
    """Parse a comma-separated report-format argument."""

    requested = [item.strip().lower() for item in value.split(",") if item.strip()]
    if not requested:
        raise ValueError("At least one report format must be specified.")

    formats: list[ReportFormat] = []
    for item in requested:
        try:
            report_format = ReportFormat(item)
        except ValueError as exc:
            valid = ", ".join(format_option.value for format_option in ReportFormat)
            raise ValueError(f"Unsupported report format: {item}. Valid formats: {valid}") from exc

        if report_format not in formats:
            formats.append(report_format)

    return tuple(formats)


def write_reports(context: ScanContext, report: AuditReport) -> list[Path]:
    """Write requested report formats and return generated paths."""

    generated: list[Path] = []

    for report_format in context.report_formats:
        if report_format == ReportFormat.MARKDOWN:
            generated.append(write_markdown_report_to_directory(report, context.output_dir))
        elif report_format == ReportFormat.JSON:
            generated.append(write_json_report_to_directory(report, context.output_dir))
        elif report_format == ReportFormat.SARIF:
            generated.append(write_sarif_report_to_directory(report, context.output_dir))

    return generated


def should_fail(level: RiskLevel, threshold: RiskLevel) -> bool:
    """Return true when the report risk level meets or exceeds the threshold."""

    return RISK_LEVEL_ORDER[level] >= RISK_LEVEL_ORDER[threshold]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    try:
        args = parse_args(argv or sys.argv[1:])
        context = build_context(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    app = ModelDueDiligenceApp()
    report = app.run(context)
    generated_paths = write_reports(context, report)

    print(f"Risk level: {report.risk_level.value}")
    print(f"Risk score: {report.risk_score}/100")
    for path in generated_paths:
        print(f"Report: {path}")

    return 1 if should_fail(report.risk_level, context.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
