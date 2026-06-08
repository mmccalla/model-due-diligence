from __future__ import annotations

import re
from pathlib import Path
from collections.abc import Iterable

from model_due_diligence.config.defaults import BINARY_STRING_MIN_LENGTH, MAX_BINARY_STRING_SCAN_BYTES
from model_due_diligence.config.suspicious_patterns import SUSPICIOUS_BINARY_STRINGS
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import is_probably_text, safe_relative


class BinaryStringScanner:
    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        findings: list[Finding] = []
        for path in files:
            if path.is_symlink() or is_probably_text(path):
                continue
            try:
                if path.stat().st_size > MAX_BINARY_STRING_SCAN_BYTES:
                    continue
                strings = self._extract_ascii_strings(path.read_bytes())
            except OSError:
                continue
            for name, pattern in SUSPICIOUS_BINARY_STRINGS.items():
                regex = re.compile(pattern, flags=re.IGNORECASE)
                for candidate in strings:
                    if regex.search(candidate):
                        findings.append(Finding(Severity.MEDIUM, f"suspicious_binary_string:{name}", safe_relative(path, context.root), f"Suspicious binary string detected: {name}", evidence=candidate[:300]))
                        break
        return findings

    @staticmethod
    def _extract_ascii_strings(data: bytes) -> list[str]:
        strings: list[str] = []
        current = bytearray()
        for byte in data:
            if 32 <= byte <= 126:
                current.append(byte)
            else:
                if len(current) >= BINARY_STRING_MIN_LENGTH:
                    strings.append(current.decode("ascii", errors="ignore"))
                current = bytearray()
        if len(current) >= BINARY_STRING_MIN_LENGTH:
            strings.append(current.decode("ascii", errors="ignore"))
        return strings
