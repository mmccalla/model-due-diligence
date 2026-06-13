"""Integration tests for suspicious fixture detection."""

from __future__ import annotations

import json
from pathlib import Path

from model_due_diligence.cli import main
from model_due_diligence.domain.models import RiskLevel

SUSPICIOUS_REPO = Path(__file__).resolve().parents[1] / "fixtures" / "suspicious_repo"


def test_cli_detects_suspicious_fixture_with_medium_risk(tmp_path: Path) -> None:
    audit_dir = tmp_path / "audit-suspicious"

    exit_code = main(
        [
            str(SUSPICIOUS_REPO),
            "--out",
            str(audit_dir),
            "--skip-external",
            "--fail-on",
            "critical",
        ]
    )

    assert exit_code == 0

    report = json.loads((audit_dir / "model_due_diligence_report.json").read_text(encoding="utf-8"))
    assert report["risk_level"] == RiskLevel.MEDIUM.value
    assert report["risk_score"] >= 30
    assert report["summary"]["high_findings"] >= 1


def test_cli_fails_on_medium_for_suspicious_fixture(tmp_path: Path) -> None:
    audit_dir = tmp_path / "audit-suspicious-fail"

    exit_code = main(
        [
            str(SUSPICIOUS_REPO),
            "--out",
            str(audit_dir),
            "--skip-external",
            "--fail-on",
            "medium",
        ]
    )

    assert exit_code == 1
