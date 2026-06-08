
"""Binary string scanner.

This scanner extracts printable ASCII strings from non-text files and searches
for suspicious indicators such as URLs, shell paths, credential variable names,
private-key markers and destructive command fragments.

It is heuristic by design. Binary string matches are review signals, not proof of
compromise.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from model_due_diligence.config.defaults import BINARY_STRING_MIN_LENGTH, MAX_BINARY_STRING_SCAN_BYTES
from model_due_diligence.config.suspicious_patterns import SUSPICIOUS_BINARY_STRINGS
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import is_probably_text, safe_relative


class BinaryStringScanner:
    """Scan binary files for suspicious printable strings."""

    scanner_name = "binary_strings"
    evidence_max_chars = 300

    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        """Scan non-text files for suspicious string indicators."""

        findings: list[Finding] = []

        for path in files:
            if self._should_skip(path):
                continue

            strings = self._read_candidate_strings(path)
            if not strings:
                continue

            findings.extend(self._scan_strings(context, path, strings))

        return findings

    @staticmethod
    def _should_skip(path: Path) -> bool:
        if path.is_symlink():
            return True
        if is_probably_text(path):
            return True

        try:
            return path.stat().st_size > MAX_BINARY_STRING_SCAN_BYTES
        except OSError:
            return True

    def _read_candidate_strings(self, path: Path) -> list[str]:
        try:
            return self._extract_ascii_strings(path.read_bytes())
        except OSError:
            return []

    def _scan_strings(self, context: ScanContext, path: Path, strings: list[str]) -> list[Finding]:
        findings: list[Finding] = []
        relative = safe_relative(path, context.root)

        for name, pattern in SUSPICIOUS_BINARY_STRINGS.items():
            regex = re.compile(pattern, flags=re.IGNORECASE)
            evidence = self._first_match(regex, strings)
            if evidence is None:
                continue

            findings.append(
                Finding(
                    severity=Severity.MEDIUM,
                    category=f"suspicious_binary_string:{name}",
                    file=relative,
                    message=f"Suspicious binary string detected: {name}.",
                    evidence=evidence[: self.evidence_max_chars],
                    recommendation="Review provenance. Binary strings alone are not proof of compromise.",
                    scanner=self.scanner_name,
                )
            )

        return findings

    @staticmethod
    def _first_match(regex: re.Pattern[str], strings: list[str]) -> str | None:
        for candidate in strings:
            if regex.search(candidate):
                return candidate
        return None

    @staticmethod
    def _extract_ascii_strings(data: bytes) -> list[str]:
        strings: list[str] = []
        current = bytearray()

        for byte in data:
            if 32 <= byte <= 126:
                current.append(byte)
                continue

            if len(current) >= BINARY_STRING_MIN_LENGTH:
                strings.append(current.decode("ascii", errors="ignore"))
            current = bytearray()

        if len(current) >= BINARY_STRING_MIN_LENGTH:
            strings.append(current.decode("ascii", errors="ignore"))

        return strings
