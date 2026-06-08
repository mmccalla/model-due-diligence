from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from model_due_diligence.app import ModelDueDiligenceApp
from model_due_diligence.config.defaults import APP_NAME, DEFAULT_TIMEOUT_SECONDS
from model_due_diligence.domain.models import RiskLevel, ScanContext
from model_due_diligence.reporting.json_report import write_json_report
from model_due_diligence.reporting.markdown_report import render_markdown
from model_due_diligence.reporting.sarif_report import write_sarif_report


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=APP_NAME, description="Static due-diligence scanner for local AI model artefacts.")
    parser.add_argument("target", help="Path to a model file or model directory.")
    parser.add_argument("--out", default="./model-audit-report", help="Output report directory.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Per-tool timeout in seconds.")
    parser.add_argument("--skip-external", action="store_true")
    parser.add_argument("--skip-modelscan", action="store_true")
    parser.add_argument("--skip-semgrep", action="store_true")
    parser.add_argument("--skip-bandit", action="store_true")
    parser.add_argument("--skip-pip-audit", action="store_true")
    parser.add_argument("--skip-detect-secrets", action="store_true")
    parser.add_argument("--skip-quality-self-check", action="store_true")
    parser.add_argument("--quality-self-check", action="store_true")
    parser.add_argument("--fail-on", choices=[level.value.lower() for level in RiskLevel], default="high")
    return parser.parse_args(argv)


def build_context(args: argparse.Namespace) -> ScanContext:
    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target does not exist: {target}")
    output_dir = Path(args.out).expanduser().resolve()
    root = target if target.is_dir() else target.parent
    return ScanContext(target, root, output_dir, args.timeout, args.skip_external, args.skip_semgrep, args.skip_bandit, args.skip_pip_audit, args.skip_detect_secrets, args.skip_modelscan, args.skip_quality_self_check, args.quality_self_check)


def should_fail(level: RiskLevel, threshold: RiskLevel) -> bool:
    order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2, RiskLevel.CRITICAL: 3}
    return order[level] >= order[threshold]


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        context = build_context(args)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    app = ModelDueDiligenceApp()
    report = app.run(context)
    json_path = context.output_dir / "model_due_diligence_report.json"
    md_path = context.output_dir / "model_due_diligence_report.md"
    sarif_path = context.output_dir / "model_due_diligence_report.sarif"
    write_json_report(report, json_path)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    write_sarif_report(report, sarif_path)
    print(f"Risk level: {report.risk_level.value}")
    print(f"Risk score: {report.risk_score}/100")
    print(f"Markdown report: {md_path}")
    print(f"JSON report: {json_path}")
    print(f"SARIF report: {sarif_path}")
    threshold = RiskLevel(args.fail_on.upper())
    return 1 if should_fail(report.risk_level, threshold) else 0
