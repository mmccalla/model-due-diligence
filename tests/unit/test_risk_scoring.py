"""Unit tests for the risk scorer."""

from __future__ import annotations

from model_due_diligence.domain.models import CommandResult, Finding, RiskLevel, Severity
from model_due_diligence.domain.risk import RiskScorer


def _finding(severity: Severity, category: str = "test_category") -> Finding:
    return Finding(
        severity=severity,
        category=category,
        file="",
        message="Test finding.",
        scanner="test_scanner",
    )


def _tool(tool: str, *, available: bool = True, exit_code: int | None = 0) -> CommandResult:
    return CommandResult(
        tool=tool,
        available=available,
        command=[tool],
        exit_code=exit_code,
    )


def test_no_findings_scores_low() -> None:
    score, level = RiskScorer().score([], [])

    assert score == 0
    assert level == RiskLevel.LOW


def test_info_findings_do_not_increase_score() -> None:
    score, level = RiskScorer().score([_finding(Severity.INFO)], [])

    assert score == 0
    assert level == RiskLevel.LOW


def test_low_findings_score_low() -> None:
    score, level = RiskScorer().score([_finding(Severity.LOW)], [])

    assert score == 3
    assert level == RiskLevel.LOW


def test_medium_findings_score_medium_when_threshold_reached() -> None:
    score, level = RiskScorer().score([_finding(Severity.MEDIUM) for _ in range(3)], [])

    assert score == 30
    assert level == RiskLevel.MEDIUM


def test_high_findings_score_high_when_threshold_reached() -> None:
    score, level = RiskScorer().score([_finding(Severity.HIGH) for _ in range(3)], [])

    assert score == 90
    assert level == RiskLevel.CRITICAL


def test_two_high_findings_score_medium_not_high() -> None:
    score, level = RiskScorer().score([_finding(Severity.HIGH) for _ in range(2)], [])

    assert score == 60
    assert level == RiskLevel.MEDIUM


def test_critical_finding_scores_high() -> None:
    score, level = RiskScorer().score([_finding(Severity.CRITICAL)], [])

    assert score == 60
    assert level == RiskLevel.MEDIUM


def test_score_is_bounded_at_100() -> None:
    score, level = RiskScorer().score([_finding(Severity.CRITICAL) for _ in range(10)], [])

    assert score == 100
    assert level == RiskLevel.CRITICAL


def test_available_non_zero_modelscan_result_increases_score() -> None:
    score, level = RiskScorer().score([], [_tool("modelscan", exit_code=1)])

    assert score == 30
    assert level == RiskLevel.MEDIUM


def test_available_non_zero_detect_secrets_result_increases_score() -> None:
    score, level = RiskScorer().score([], [_tool("detect-secrets", exit_code=1)])

    assert score == 20
    assert level == RiskLevel.LOW


def test_unknown_non_zero_tool_uses_default_weight() -> None:
    score, level = RiskScorer().score([], [_tool("unknown-tool", exit_code=99)])

    assert score == RiskScorer.DEFAULT_TOOL_NON_ZERO_WEIGHT
    assert level == RiskLevel.LOW


def test_missing_tool_does_not_increase_score_directly() -> None:
    score, level = RiskScorer().score([], [_tool("modelscan", available=False, exit_code=None)])

    assert score == 0
    assert level == RiskLevel.LOW


def test_zero_exit_tool_does_not_increase_score() -> None:
    score, level = RiskScorer().score([], [_tool("modelscan", exit_code=0)])

    assert score == 0
    assert level == RiskLevel.LOW


def test_findings_and_tool_scores_are_combined() -> None:
    score, level = RiskScorer().score(
        [_finding(Severity.MEDIUM), _finding(Severity.HIGH)],
        [_tool("detect-secrets", exit_code=1)],
    )

    assert score == 60
    assert level == RiskLevel.MEDIUM
