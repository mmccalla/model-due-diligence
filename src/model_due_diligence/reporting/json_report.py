"""JSON report writer.

The JSON report is the stable machine-readable output for automation,
regression tests and downstream tooling. It should remain deterministic,
readable and safe to serialise from the domain dataclasses.
"""

from __future__ import annotations

import dataclasses
import json
from enum import Enum
from pathlib import Path
from typing import Any

from model_due_diligence.config.defaults import REPORT_JSON_FILENAME
from model_due_diligence.domain.models import AuditReport


class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder for dataclasses, enums and paths used in reports."""

    def default(self, value: object) -> Any:
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            return dataclasses.asdict(value)

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, Path):
            return str(value)

        return super().default(value)


def write_json_report(report: AuditReport, path: Path) -> None:
    """Write an audit report to a specific JSON file path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_json(report), encoding="utf-8")


def write_json_report_to_directory(report: AuditReport, output_dir: Path) -> Path:
    """Write the standard JSON report into an output directory."""

    output_path = output_dir / REPORT_JSON_FILENAME
    write_json_report(report, output_path)
    return output_path


def to_json(report: AuditReport) -> str:
    """Serialise an audit report to deterministic pretty JSON."""

    return json.dumps(
        report,
        cls=EnhancedJSONEncoder,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )
