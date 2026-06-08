from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from collections.abc import Iterable

from model_due_diligence.config.defaults import MODEL_EXTENSIONS
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import safe_relative


class EntropyScanner:
    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        findings: list[Finding] = []
        for path in files:
            if path.is_symlink() or path.suffix.lower() in MODEL_EXTENSIONS:
                continue
            try:
                size = path.stat().st_size
                if size == 0 or size > 10_000_000:
                    continue
                entropy = self._shannon_entropy(path.read_bytes())
            except OSError:
                continue
            if entropy > 7.8:
                findings.append(Finding(Severity.LOW, "high_entropy_non_model_file", safe_relative(path, context.root), f"High entropy file detected outside expected model formats: {entropy:.2f}"))
        return findings

    @staticmethod
    def _shannon_entropy(data: bytes) -> float:
        if not data:
            return 0.0
        counts = Counter(data)
        length = len(data)
        return -sum((count / length) * math.log2(count / length) for count in counts.values())
