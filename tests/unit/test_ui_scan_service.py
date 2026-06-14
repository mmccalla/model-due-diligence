"""Unit tests for UI scan orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers_ollama import build_fake_ollama_store

from model_due_diligence.domain.models import AuditReport, AuditSummary, CommandResult, RiskLevel, ScanContext
from model_due_diligence.ui.scan_service import preview_scan, run_scan
from model_due_diligence.ui.schemas import InteractionState, ScanOptions, ScanTargetRequest, ScanTargetType


def test_preview_scan_raises_for_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.gguf"
    request = ScanTargetRequest(target_type=ScanTargetType.PATH, target=str(missing))

    with pytest.raises(FileNotFoundError, match="does not exist"):
        preview_scan(request)


def test_run_scan_serialises_report_for_path_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    request = ScanTargetRequest(
        target_type=ScanTargetType.PATH,
        target=str(repo),
        options=ScanOptions(skip_external=False),
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

    response = run_scan(request, tmp_path / "out", scan_id="a" * 32, runner=fake_runner)

    assert response.state == InteractionState.SUCCESS
    assert response.report["risk_level"] == RiskLevel.LOW.value
    assert response.report_paths.scan_id == "a" * 32
    assert response.report_paths.markdown_path is not None


def test_run_scan_reports_partial_success_when_tool_failed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    request = ScanTargetRequest(target_type=ScanTargetType.PATH, target=str(repo))

    def fake_runner(_: ScanContext) -> AuditReport:
        return AuditReport(
            scanned_path=str(repo),
            generated_at_utc="2026-01-01T00:00:00+00:00",
            files=[],
            metadata=[],
            findings=[],
            tools=[CommandResult(tool="semgrep", available=False, command=["semgrep"])],
            risk_score=0,
            risk_level=RiskLevel.LOW,
            summary=AuditSummary(files_scanned=1, findings=0),
        )

    response = run_scan(request, tmp_path / "out", scan_id="b" * 32, runner=fake_runner)

    assert response.state == InteractionState.PARTIAL_SUCCESS


def test_run_scan_reports_warning_when_external_scanners_skipped(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    request = ScanTargetRequest(
        target_type=ScanTargetType.PATH,
        target=str(repo),
        options=ScanOptions(skip_external=True),
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

    response = run_scan(request, tmp_path / "out", scan_id="c" * 32, runner=fake_runner)

    assert response.state == InteractionState.WARNING
    assert response.warnings


def test_preview_scan_for_ollama_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    models_dir = build_fake_ollama_store(tmp_path, "qwen3:4b")
    monkeypatch.setenv("OLLAMA_MODELS", str(models_dir))
    request = ScanTargetRequest(target_type=ScanTargetType.OLLAMA, target="qwen3:4b")

    response = preview_scan(request)

    assert response.state == InteractionState.SUCCESS
    assert response.target_type == ScanTargetType.OLLAMA
    assert response.items
