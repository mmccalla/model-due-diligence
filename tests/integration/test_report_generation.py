"""Report generation integration tests.

These tests verify that the report renderers accept the current domain model and
produce the expected Markdown, JSON and SARIF artefacts without running external
scanner tools.
"""

from __future__ import annotations

import json
from pathlib import Path

from model_due_diligence.domain.models import AuditReport, AuditSummary, Finding, RiskLevel, Severity
from model_due_diligence.reporting.json_report import to_json, write_json_report_to_directory
from model_due_diligence.reporting.markdown_report import render_markdown, write_markdown_report_to_directory
from model_due_diligence.reporting.sarif_report import to_sarif, write_sarif_report_to_directory


def _sample_report() -> AuditReport:
    finding = Finding(
        severity=Severity.MEDIUM,
        category="test_category",
        file="README.md",
        message="Test finding message.",
        evidence="test evidence",
        recommendation="Review the test finding.",
        scanner="test_scanner",
    )

    return AuditReport(
        scanned_path="tests/fixtures/safe_repo",
        generated_at_utc="2026-01-01T00:00:00+00:00",
        files=[],
        metadata=[],
        findings=[finding],
        tools=[],
        risk_score=30,
        risk_level=RiskLevel.MEDIUM,
        summary=AuditSummary(
            files_scanned=0,
            findings=1,
            medium_findings=1,
            external_tools_run=0,
            file_categories={},
            git={"is_git_repo": False},
        ),
    )


def test_markdown_report_renders_current_domain_model() -> None:
    markdown = render_markdown(_sample_report())

    assert "Model Due Diligence Report" in markdown
    assert "**Risk level:** **MEDIUM**" in markdown
    assert "test_scanner" in markdown
    assert "test_category" in markdown
    assert "Use generated reports as review evidence" in markdown


def test_json_report_serialises_current_domain_model() -> None:
    payload = json.loads(to_json(_sample_report()))

    assert payload["risk_level"] == "MEDIUM"
    assert payload["summary"]["findings"] == 1
    assert payload["findings"][0]["scanner"] == "test_scanner"
    assert payload["findings"][0]["severity"] == "MEDIUM"


def test_sarif_report_serialises_findings() -> None:
    sarif = to_sarif(_sample_report())
    run = sarif["runs"][0]

    assert sarif["version"] == "2.1.0"
    assert run["invocations"][0]["properties"]["riskLevel"] == "MEDIUM"
    assert run["results"][0]["ruleId"] == "test_scanner/test_category"
    assert run["results"][0]["level"] == "warning"


def test_report_writers_create_expected_files(tmp_path: Path) -> None:
    report = _sample_report()

    markdown_path = write_markdown_report_to_directory(report, tmp_path)
    json_path = write_json_report_to_directory(report, tmp_path)
    sarif_path = write_sarif_report_to_directory(report, tmp_path)

    assert markdown_path.exists()
    assert json_path.exists()
    assert sarif_path.exists()
    assert markdown_path.name == "model_due_diligence_report.md"
    assert json_path.name == "model_due_diligence_report.json"
    assert sarif_path.name == "model_due_diligence_report.sarif"
