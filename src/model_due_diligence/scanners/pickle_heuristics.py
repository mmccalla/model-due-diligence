"""Pickle heuristic scanner.

This scanner performs a lightweight static byte-pattern check for risky
pickle-like markers inside high-risk serialisation formats. It is an additional
belt-and-braces check alongside ModelScan, not a replacement for a specialised
model serialisation scanner.

The scanner does not deserialize or execute artefacts. A match is a review
signal, not proof of compromise.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from model_due_diligence.config.defaults import HIGH_RISK_SERIALISATION_EXTENSIONS, MAX_BINARY_STRING_SCAN_BYTES
from model_due_diligence.config.suspicious_patterns import RISKY_PICKLE_MARKERS
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import safe_relative


class PickleHeuristicScanner:
    """Scan high-risk serialised artefacts for risky pickle-like byte markers."""

    scanner_name = "pickle_heuristics"
    evidence_max_chars = 300

    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        """Return findings for high-risk serialisation files containing risky markers."""

        findings: list[Finding] = []

        for path in files:
            if self._should_skip(path):
                continue

            data = self._read_candidate_bytes(path)
            if data is None:
                continue

            marker = self._first_marker(data)
            if marker is None:
                continue

            findings.append(self._risky_marker_finding(context, path, marker))

        return findings

    @staticmethod
    def _should_skip(path: Path) -> bool:
        if path.is_symlink():
            return True
        return path.suffix.lower() not in HIGH_RISK_SERIALISATION_EXTENSIONS

    @staticmethod
    def _read_candidate_bytes(path: Path) -> bytes | None:
        try:
            return path.read_bytes()[:MAX_BINARY_STRING_SCAN_BYTES]
        except OSError:
            return None

    @staticmethod
    def _first_marker(data: bytes) -> bytes | None:
        for marker in RISKY_PICKLE_MARKERS:
            if marker in data:
                return marker
        return None

    def _risky_marker_finding(self, context: ScanContext, path: Path, marker: bytes) -> Finding:
        return Finding(
            severity=Severity.HIGH,
            category="pickle_heuristic_risky_marker",
            file=safe_relative(path, context.root),
            message="Risky pickle-like marker detected in a high-risk serialisation artefact.",
            evidence=repr(marker)[: self.evidence_max_chars],
            recommendation=(
                "Do not load this artefact until the marker is reviewed. Use ModelScan output, provenance checks "
                "and manual review before deciding whether this is acceptable."
            ),
            scanner=self.scanner_name,
        )
