"""Unit tests for security documentation posture."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SECURITY_MD = REPO_ROOT / "SECURITY.md"


@pytest.fixture(name="security_text")
def fixture_security_text() -> str:
    return SECURITY_MD.read_text(encoding="utf-8")


def test_security_md_documents_audit_pii_posture(security_text: str) -> None:
    lowered = security_text.lower()
    assert "pii" in lowered or "audit" in lowered


def test_security_md_documents_mdd_ui_localhost_posture(security_text: str) -> None:
    lowered = security_text.lower()
    assert "mdd-ui" in lowered
    assert "127.0.0.1" in security_text or "localhost" in lowered
