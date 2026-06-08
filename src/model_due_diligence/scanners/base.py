from __future__ import annotations

from typing import Protocol

from model_due_diligence.domain.models import Finding, ScanContext


class Scanner(Protocol):
    def scan(self, context: ScanContext) -> list[Finding]: ...
