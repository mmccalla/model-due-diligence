from __future__ import annotations

from model_due_diligence.domain.models import CommandResult, Finding, RiskLevel, Severity


class RiskScorer:
    SEVERITY_WEIGHTS = {Severity.INFO: 0, Severity.LOW: 3, Severity.MEDIUM: 10, Severity.HIGH: 30, Severity.CRITICAL: 60}
    TOOL_FINDING_HINTS = {"modelscan": 30, "semgrep": 10, "bandit": 10, "pip-audit": 10, "detect-secrets": 20, "self_ruff_check": 3, "self_ruff_format_check": 3, "self_pyright": 3, "self_mypy": 3}

    def score(self, findings: list[Finding], tools: list[CommandResult]) -> tuple[int, RiskLevel]:
        score = sum(self.SEVERITY_WEIGHTS[f.severity] for f in findings)
        for tool in tools:
            if tool.available and tool.exit_code not in (0, None):
                score += self.TOOL_FINDING_HINTS.get(tool.tool, 5)
        score = min(score, 100)
        if score >= 90: return score, RiskLevel.CRITICAL
        if score >= 70: return score, RiskLevel.HIGH
        if score >= 30: return score, RiskLevel.MEDIUM
        return score, RiskLevel.LOW
