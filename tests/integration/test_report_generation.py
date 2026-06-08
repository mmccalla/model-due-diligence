from pathlib import Path
from model_due_diligence.domain.models import AuditReport, RiskLevel
from model_due_diligence.reporting.markdown_report import render_markdown


def test_markdown_report_renders() -> None:
    report = AuditReport("x", "now", [], [], [], [], 0, RiskLevel.LOW, {"files_scanned": 0})
    assert "Model Due Diligence Report" in render_markdown(report)
