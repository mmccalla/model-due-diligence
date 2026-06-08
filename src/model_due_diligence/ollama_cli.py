"""CLI entry point for scanning installed Ollama models by name."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from model_due_diligence.app import ModelDueDiligenceApp
from model_due_diligence.cli import parse_report_formats, should_fail, write_reports
from model_due_diligence.config.defaults import DEFAULT_FAIL_ON, DEFAULT_OUTPUT_DIRECTORY, DEFAULT_TIMEOUT_SECONDS
from model_due_diligence.domain.models import AuditReport, RiskLevel, ScanContext
from model_due_diligence.ollama import DEFAULT_OLLAMA_MODELS_DIR, resolve_installed_model, stage_model_for_scan

APP_NAME = "mdd-ollama"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Resolve an installed Ollama model by name and run static due diligence on its local artefacts.",
    )
    parser.add_argument("model", help="Installed Ollama model name, for example llama3:8b.")
    parser.add_argument(
        "--ollama-models-dir",
        default=str(DEFAULT_OLLAMA_MODELS_DIR),
        help=f"Ollama models directory. Default: {DEFAULT_OLLAMA_MODELS_DIR}",
    )
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
        "--keep-staged",
        action="store_true",
        help="Keep the temporary staged Ollama scan directory instead of deleting it after the scan.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        models_dir = Path(args.ollama_models_dir).expanduser().resolve()
        resolved = resolve_installed_model(args.model, models_dir=models_dir)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    staged_path, temp_dir = stage_model_for_scan(resolved, keep_directory=args.keep_staged)
    try:
        context = ScanContext(
            target=staged_path,
            root=staged_path,
            output_dir=Path(args.out).expanduser().resolve(),
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

        report = ModelDueDiligenceApp().run(context)
        report = _replace_scanned_path(report, f"ollama:{args.model}")
        generated_paths = write_reports(context, report)

        print(f"Resolved model: {args.model}")
        print(f"Manifest: {resolved.manifest_path}")
        print(f"Staged scan directory: {staged_path}")
        print(f"Risk level: {report.risk_level.value}")
        print(f"Risk score: {report.risk_score}/100")
        for path in generated_paths:
            print(f"Report: {path}")

        return 1 if should_fail(report.risk_level, context.fail_on) else 0
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def _replace_scanned_path(report: AuditReport, scanned_path: str) -> AuditReport:
    return replace(report, scanned_path=scanned_path)


if __name__ == "__main__":
    raise SystemExit(main())
