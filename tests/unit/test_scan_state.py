"""Unit tests for scan interaction state derivation."""

from __future__ import annotations

from model_due_diligence.domain.models import AuditReport, AuditSummary, CommandResult, RiskLevel
from model_due_diligence.ui.scan_state import derive_scan_interaction_state
from model_due_diligence.ui.schemas import InteractionState


def _empty_report(*, tools: list[CommandResult] | None = None) -> AuditReport:
    return AuditReport(
        scanned_path="/tmp",
        generated_at_utc="2026-01-01T00:00:00+00:00",
        files=[],
        metadata=[],
        findings=[],
        tools=tools or [],
        risk_score=0,
        risk_level=RiskLevel.LOW,
        summary=AuditSummary(files_scanned=0, findings=0),
    )


def test_derive_scan_state_success_without_warnings() -> None:
    state = derive_scan_interaction_state(_empty_report(), [])

    assert state == InteractionState.SUCCESS


def test_derive_scan_state_warning_when_configuration_warnings_present() -> None:
    state = derive_scan_interaction_state(_empty_report(), ["External scanners were skipped for this run."])

    assert state == InteractionState.WARNING


def test_derive_scan_state_partial_success_when_tool_unavailable() -> None:
    report = _empty_report(tools=[CommandResult(tool="bandit", available=False, command=["bandit"])])
    state = derive_scan_interaction_state(report, [])

    assert state == InteractionState.PARTIAL_SUCCESS
