from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from model_due_diligence.domain.models import AuditReport


def write_json_report(report: AuditReport, path: Path) -> None:
    path.write_text(json.dumps(dataclasses.asdict(report), indent=2, ensure_ascii=False), encoding="utf-8")
