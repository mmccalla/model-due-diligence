"""Unit tests for UI scan orchestration."""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.domain.models import AuditReport, AuditSummary, RiskLevel, ScanContext
from model_due_diligence.ui.scan_service import preview_scan, run_scan
from model_due_diligence.ui.schemas import InteractionState, ScanTargetRequest, ScanTargetType


def test_preview_scan_returns_error_for_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.gguf"
    request = ScanTargetRequest(target_type=ScanTargetType.PATH, target=str(missing))

    response = preview_scan(request)

    assert response.state == InteractionState.ERROR
    assert "does not exist" in response.message


def test_run_scan_serialises_report_for_path_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    request = ScanTargetRequest(
        target_type=ScanTargetType.PATH,
        target=str(repo),
    )

    def fake_runner(_: ScanContext) -> AuditReport:
        return AuditReport(
            scanned_path=str(repo),
            generated_at_utc="2026-01-01T00:00:00+00:00",
            files=[],
            metadata=[],
            findings=[],
            tools=[],
            risk_score=0,
            risk_level=RiskLevel.LOW,
            summary=AuditSummary(files_scanned=1, findings=0),
        )

    response = run_scan(request, tmp_path / "out", runner=fake_runner)

    assert response.state == InteractionState.SUCCESS
    assert response.report["risk_level"] == RiskLevel.LOW.value
    assert response.report_paths.markdown_path is not None
