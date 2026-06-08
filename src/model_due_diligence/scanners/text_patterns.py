"""Suspicious text pattern scanner.

This scanner searches text-like files for conservative indicators of risky
behaviour: shell execution, network access, destructive commands, credential
access, obfuscation, dynamic download-and-execute patterns and unsafe model
loading options.

The scanner does not execute files. Findings are review signals, not proof of
compromise.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from model_due_diligence.config.suspicious_patterns import SUSPICIOUS_TEXT_PATTERNS
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import is_probably_text, read_text_safely, safe_relative


class SuspiciousTextScanner:
    """Scan text-like files for suspicious static patterns."""

    scanner_name = "text_patterns"
    evidence_context_chars = 100

    HIGH_SEVERITY_PATTERNS: frozenset[str] = frozenset(
        {
            "transformers_remote_code",
            "dynamic_download_and_execute",
            "reverse_shell",
        }
    )

    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        """Return findings for suspicious text patterns in text-like files."""

        findings: list[Finding] = []

        for path in files:
            if self._should_skip(path):
                continue

            text = read_text_safely(path)
            if text is None:
                continue

            relative = safe_relative(path, context.root)
            findings.extend(self._scan_text(relative, text))

        return findings

    @staticmethod
    def _should_skip(path: Path) -> bool:
        return path.is_symlink() or not is_probably_text(path)

    def _scan_text(self, relative: str, text: str) -> list[Finding]:
        findings: list[Finding] = []

        for name, pattern in SUSPICIOUS_TEXT_PATTERNS.items():
            match = self._first_match(pattern, text)
            if match is None:
                continue

            findings.append(self._finding_for_match(relative, text, name, match))

        return findings

    @staticmethod
    def _first_match(pattern: str, text: str) -> re.Match[str] | None:
        return next(re.finditer(pattern, text, flags=re.IGNORECASE), None)

    def _finding_for_match(self, relative: str, text: str, name: str, match: re.Match[str]) -> Finding:
        return Finding(
            severity=self._severity_for_pattern(name),
            category=f"suspicious_text:{name}",
            file=relative,
            message=f"Suspicious text pattern detected: {name}.",
            evidence=self._evidence(text, match),
            recommendation=self._recommendation_for_pattern(name),
            scanner=self.scanner_name,
        )

    def _evidence(self, text: str, match: re.Match[str]) -> str:
        start = max(0, match.start() - self.evidence_context_chars)
        end = min(len(text), match.end() + self.evidence_context_chars)
        return text[start:end].replace("\n", "\\n")

    def _severity_for_pattern(self, name: str) -> Severity:
        if name in self.HIGH_SEVERITY_PATTERNS:
            return Severity.HIGH
        return Severity.MEDIUM

    @staticmethod
    def _recommendation_for_pattern(name: str) -> str:
        recommendations = {
            "transformers_remote_code": (
                "Avoid trust_remote_code=True unless the repository code has been manually reviewed and the source "
                "is trusted. Treat it as executable code."
            ),
            "dynamic_download_and_execute": (
                "Review immediately. Download-and-execute patterns are high-risk in model repositories and should "
                "not run during setup or model loading."
            ),
            "reverse_shell": "Review immediately. Reverse-shell indicators are high-risk and unexpected in model repositories.",
            "secret_terms": "Check whether real credentials are present. If so, remove them and rotate the affected secrets.",
            "credential_file_access": "Review whether the repository attempts to read local credential files or environment material.",
            "network_access": "Review whether network access is expected and whether it can execute during setup or model loading.",
            "shell_execution": "Review whether shell execution can occur during import, setup or model loading.",
            "destructive_file_ops": "Review whether destructive file operations can affect user files or project repositories.",
            "obfuscation": "Review whether obfuscation is justified. Obfuscated execution paths require manual inspection.",
            "environment_access": "Review whether environment access can expose secrets or local configuration.",
            "package_install": "Review whether dependency installation is explicit, pinned and safe for the intended environment.",
        }
        return recommendations.get(name, "Manually review whether this can execute during model loading or setup.")
