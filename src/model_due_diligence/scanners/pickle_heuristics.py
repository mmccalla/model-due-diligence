from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable

from model_due_diligence.config.defaults import HIGH_RISK_SERIALISATION_EXTENSIONS, MAX_BINARY_STRING_SCAN_BYTES
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import safe_relative


class PickleHeuristicScanner:
    RISKY_PICKLE_MARKERS = [b"cos\nsystem\n", b"posix\nsystem\n", b"subprocess\n", b"os\nsystem\n", b"builtins\neval\n", b"builtins\nexec\n", b"GLOBAL", b"REDUCE"]

    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        findings: list[Finding] = []
        for path in files:
            if path.suffix.lower() not in HIGH_RISK_SERIALISATION_EXTENSIONS or path.is_symlink():
                continue
            try:
                data = path.read_bytes()[:MAX_BINARY_STRING_SCAN_BYTES]
            except OSError:
                continue
            for marker in self.RISKY_PICKLE_MARKERS:
                if marker in data:
                    findings.append(Finding(Severity.HIGH, "pickle_heuristic_risky_marker", safe_relative(path, context.root), "Risky pickle-like marker detected.", evidence=repr(marker), recommendation="Do not load. Use ModelScan output and manual review."))
                    break
        return findings
