"""Scanner protocol definitions.

Native scanners perform static inspection without executing model artefacts,
repository code or model-loading paths. They return normalised domain findings
and, where relevant, extracted model metadata.
"""

from __future__ import annotations

from typing import Protocol

from model_due_diligence.domain.models import Finding, ModelMetadata, ScanContext, ScannerResult


class Scanner(Protocol):
    """Protocol for native static scanners.

    Implementations should be deterministic, side-effect limited and static by
    default. A finding is evidence for review, not proof of compromise.
    """

    scanner_name: str

    def scan(self, context: ScanContext) -> list[Finding]:
        """Scan a target and return normalised findings."""
        ...


class MetadataScanner(Protocol):
    """Protocol for native scanners that also extract model metadata."""

    scanner_name: str

    def scan(self, context: ScanContext) -> tuple[list[ModelMetadata], list[Finding]]:
        """Scan a target and return metadata plus normalised findings."""
        ...


class ResultScanner(Protocol):
    """Protocol for scanners that return the richer `ScannerResult` envelope."""

    scanner_name: str

    def scan(self, context: ScanContext) -> ScannerResult:
        """Scan a target and return a normalised scanner result envelope."""
        ...
