from model_due_diligence.domain.models import Finding, Severity
from model_due_diligence.domain.risk import RiskScorer


def test_high_finding_scores_high() -> None:
    score, level = RiskScorer().score([Finding(Severity.HIGH, "x", "", "msg") for _ in range(3)], [])
    assert score >= 70
    assert level.value in {"HIGH", "CRITICAL"}
