from __future__ import annotations

import re
from pathlib import Path
from collections.abc import Iterable

from model_due_diligence.config.suspicious_patterns import SUSPICIOUS_TEXT_PATTERNS
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import is_probably_text, read_text_safely, safe_relative


class SuspiciousTextScanner:
    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        findings: list[Finding] = []
        for path in files:
            if not is_probably_text(path) or path.is_symlink():
                continue
            text = read_text_safely(path)
            if text is None:
                continue
            findings.extend(self._scan_text(safe_relative(path, context.root), text))
        return findings

    @staticmethod
    def _scan_text(relative: str, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for name, pattern in SUSPICIOUS_TEXT_PATTERNS.items():
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                evidence = text[max(0, match.start() - 100): min(len(text), match.end() + 100)].replace("\n", "\\n")
                severity = Severity.HIGH if name == "transformers_remote_code" else Severity.MEDIUM
                findings.append(Finding(severity, f"suspicious_text:{name}", relative, f"Suspicious text pattern detected: {name}", evidence=evidence, recommendation="Manually review whether this can execute during model loading or setup."))
                break
        return findings
