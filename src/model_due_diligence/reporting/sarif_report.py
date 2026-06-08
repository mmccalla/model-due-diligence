from __future__ import annotations

import json
from pathlib import Path

from model_due_diligence.domain.models import AuditReport


def write_sarif_report(report: AuditReport, path: Path) -> None:
    results = []
    for finding in report.findings:
        results.append({
            "ruleId": finding.category,
            "level": "error" if finding.severity.value in {"HIGH", "CRITICAL"} else "warning",
            "message": {"text": finding.message},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": finding.file or "<repository>"}}}],
        })
    sarif = {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": [{"tool": {"driver": {"name": "model-due-diligence"}}, "results": results}]}
    path.write_text(json.dumps(sarif, indent=2), encoding="utf-8")
