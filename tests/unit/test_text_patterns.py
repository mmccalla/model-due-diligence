from model_due_diligence.scanners.text_patterns import SuspiciousTextScanner


def test_text_scanner_flags_eval() -> None:
    findings = SuspiciousTextScanner._scan_text("x.py", "eval('1+1')")
    assert findings
