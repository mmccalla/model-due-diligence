"""Entropy scanner.

This scanner identifies unusually high-entropy non-model files. High entropy can
indicate compressed, encrypted, packed or otherwise unusual content that merits
manual review when it appears outside expected model artefact formats.

Model weight files are deliberately excluded because they are expected to have
high entropy.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from model_due_diligence.config.defaults import MODEL_EXTENSIONS
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import safe_relative


class EntropyScanner:
    """Scan non-model files for high-entropy anomalies."""

    scanner_name = "entropy"
    max_file_size_bytes = 10_000_000
    entropy_threshold = 7.8

    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        """Return findings for high-entropy non-model files."""

        findings: list[Finding] = []

        for path in files:
            if self._should_skip(path):
                continue

            entropy = self._entropy_for_file(path)
            if entropy is None or entropy <= self.entropy_threshold:
                continue

            findings.append(self._high_entropy_finding(context, path, entropy))

        return findings

    def _should_skip(self, path: Path) -> bool:
        if path.is_symlink():
            return True
        if path.suffix.lower() in MODEL_EXTENSIONS:
            return True

        try:
            size = path.stat().st_size
        except OSError:
            return True

        return size == 0 or size > self.max_file_size_bytes

    def _entropy_for_file(self, path: Path) -> float | None:
        try:
            return self._shannon_entropy(path.read_bytes())
        except OSError:
            return None

    def _high_entropy_finding(self, context: ScanContext, path: Path, entropy: float) -> Finding:
        return Finding(
            severity=Severity.LOW,
            category="high_entropy_non_model_file",
            file=safe_relative(path, context.root),
            message=f"High entropy file detected outside expected model formats: {entropy:.2f}.",
            evidence=f"entropy={entropy:.4f}; threshold={self.entropy_threshold}",
            recommendation=(
                "Review whether this file is expected compressed, encrypted or binary content. "
                "High entropy alone is not proof of compromise."
            ),
            scanner=self.scanner_name,
        )

    @staticmethod
    def _shannon_entropy(data: bytes) -> float:
        """Calculate Shannon entropy for a byte sequence."""

        if not data:
            return 0.0

        counts = Counter(data)
        length = len(data)
        return -sum((count / length) * math.log2(count / length) for count in counts.values())
