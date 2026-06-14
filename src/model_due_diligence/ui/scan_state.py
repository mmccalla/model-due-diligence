"""Derive UI interaction states from completed scan reports."""

from __future__ import annotations

from model_due_diligence.domain.models import AuditReport, CommandResult
from model_due_diligence.ui.schemas import InteractionState


def derive_scan_interaction_state(report: AuditReport, warnings: list[str]) -> InteractionState:
    """Map scanner outcomes to a frontend-visible interaction state."""

    if _has_tool_execution_issues(report.tools):
        return InteractionState.PARTIAL_SUCCESS
    if warnings:
        return InteractionState.WARNING
    return InteractionState.SUCCESS


def _has_tool_execution_issues(tools: list[CommandResult]) -> bool:
    for tool in tools:
        if not tool.available:
            return True
        if tool.exit_code is not None and tool.exit_code != 0:
            return True
    return False
