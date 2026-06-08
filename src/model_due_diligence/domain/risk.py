"""Risk scoring for model-due-diligence.

The scorer converts normalised findings and external tool outcomes into a
bounded risk score and risk level. It is intentionally conservative and should
be treated as a decision aid, not an automated trust verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from model_due_diligence.domain.models import CommandResult, Finding, RiskLevel, Severity


@dataclass(frozen=True, slots=True)
class RiskBand:
    """Inclusive lower-bound mapping from score to risk level."""

    minimum_score: int
    risk_level: RiskLevel


class RiskScorer:
    """Score findings and external scanner results into a bounded risk level."""

    MIN_SCORE = 0
    MAX_SCORE = 100

    SEVERITY_WEIGHTS: ClassVar[dict[Severity, int]] = {
        Severity.INFO: 0,
        Severity.LOW: 3,
        Severity.MEDIUM: 10,
        Severity.HIGH: 30,
        Severity.CRITICAL: 60,
    }

    TOOL_FINDING_HINTS: ClassVar[dict[str, int]] = {
        "modelscan": 30,
        "semgrep": 10,
        "bandit": 10,
        "pip-audit": 10,
        "detect-secrets": 20,
        "self_ruff_check": 3,
        "self_ruff_format_check": 3,
        "self_pyright": 3,
        "self_mypy": 3,
    }

    RISK_BANDS: ClassVar[tuple[RiskBand, ...]] = (
        RiskBand(90, RiskLevel.CRITICAL),
        RiskBand(70, RiskLevel.HIGH),
        RiskBand(30, RiskLevel.MEDIUM),
        RiskBand(0, RiskLevel.LOW),
    )

    DEFAULT_TOOL_NON_ZERO_WEIGHT = 5

    def score(self, findings: list[Finding], tools: list[CommandResult]) -> tuple[int, RiskLevel]:
        """Return bounded score and risk level for findings and tool outcomes."""

        raw_score = self._score_findings(findings) + self._score_tools(tools)
        bounded_score = self._bound_score(raw_score)
        return bounded_score, self._risk_level_for_score(bounded_score)

    def _score_findings(self, findings: list[Finding]) -> int:
        return sum(self.SEVERITY_WEIGHTS[finding.severity] for finding in findings)

    def _score_tools(self, tools: list[CommandResult]) -> int:
        score = 0

        for tool in tools:
            if not self._tool_has_reviewable_signal(tool):
                continue

            score += self.TOOL_FINDING_HINTS.get(tool.tool, self.DEFAULT_TOOL_NON_ZERO_WEIGHT)

        return score

    @staticmethod
    def _tool_has_reviewable_signal(tool: CommandResult) -> bool:
        """Return true when an external tool outcome should influence risk.

        Missing tools are recorded elsewhere as findings. Here we only score
        available tools whose non-zero exit codes indicate findings or execution
        problems requiring review.
        """

        return tool.available and tool.exit_code not in (0, None)

    def _risk_level_for_score(self, score: int) -> RiskLevel:
        for band in self.RISK_BANDS:
            if score >= band.minimum_score:
                return band.risk_level

        return RiskLevel.LOW

    def _bound_score(self, score: int) -> int:
        return max(self.MIN_SCORE, min(score, self.MAX_SCORE))
