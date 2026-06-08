"""SARIF report writer.

SARIF output is intended for GitHub code scanning and other tooling that can
consume static-analysis results. The SARIF report mirrors normalised findings
from the audit report; it does not include raw external scanner artefacts.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from model_due_diligence.config.defaults import APP_NAME, REPORT_SARIF_FILENAME
from model_due_diligence.domain.models import AuditReport, Finding, Severity
from model_due_diligence.reporting.json_report import EnhancedJSONEncoder

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
REPOSITORY_LOCATION = "<repository>"


def write_sarif_report(report: AuditReport, path: Path) -> None:
    """Write an audit report to a specific SARIF file path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_sarif_json(report), encoding="utf-8")


def write_sarif_report_to_directory(report: AuditReport, output_dir: Path) -> Path:
    """Write the standard SARIF report into an output directory."""

    output_path = output_dir / REPORT_SARIF_FILENAME
    write_sarif_report(report, output_path)
    return output_path


def to_sarif_json(report: AuditReport) -> str:
    """Serialise an audit report to deterministic pretty SARIF JSON."""

    return json.dumps(
        to_sarif(report),
        cls=EnhancedJSONEncoder,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def to_sarif(report: AuditReport) -> dict[str, Any]:
    """Convert an audit report into a SARIF 2.1.0 document."""

    rules = _build_rules(report.findings)

    return {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": APP_NAME,
                        "informationUri": "https://github.com/",
                        "rules": rules,
                    }
                },
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "properties": {
                            "riskLevel": _enum_value(report.risk_level),
                            "riskScore": report.risk_score,
                            "scannedPath": report.scanned_path,
                            "generatedAtUtc": report.generated_at_utc,
                        },
                    }
                ],
                "results": [_finding_to_result(finding) for finding in report.findings],
            }
        ],
    }


def _build_rules(findings: list[Finding]) -> list[dict[str, Any]]:
    rules_by_id: dict[str, dict[str, Any]] = {}

    for finding in findings:
        rule_id = _rule_id(finding)
        if rule_id in rules_by_id:
            continue

        rules_by_id[rule_id] = {
            "id": rule_id,
            "name": finding.category,
            "shortDescription": {"text": finding.category.replace("_", " ").title()},
            "fullDescription": {"text": finding.recommendation or finding.message},
            "defaultConfiguration": {
                "level": _sarif_level(finding.severity),
            },
            "properties": {
                "scanner": finding.scanner or APP_NAME,
                "severity": finding.severity.value,
                "category": finding.category,
            },
        }

    return sorted(rules_by_id.values(), key=lambda rule: str(rule["id"]))


def _finding_to_result(finding: Finding) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ruleId": _rule_id(finding),
        "level": _sarif_level(finding.severity),
        "message": {"text": finding.message},
        "locations": [_location_for_finding(finding)],
        "properties": {
            "scanner": finding.scanner or APP_NAME,
            "severity": finding.severity.value,
            "category": finding.category,
        },
    }

    if finding.evidence:
        result["properties"]["evidence"] = finding.evidence

    if finding.recommendation:
        result["properties"]["recommendation"] = finding.recommendation

    return result


def _location_for_finding(finding: Finding) -> dict[str, Any]:
    return {
        "physicalLocation": {
            "artifactLocation": {
                "uri": _normalise_uri(finding.file),
            }
        }
    }


def _rule_id(finding: Finding) -> str:
    scanner = finding.scanner or APP_NAME
    return f"{scanner}/{finding.category}"


def _sarif_level(severity: Severity) -> str:
    if severity in {Severity.CRITICAL, Severity.HIGH}:
        return "error"
    if severity == Severity.MEDIUM:
        return "warning"
    return "note"


def _normalise_uri(file_path: str) -> str:
    if not file_path:
        return REPOSITORY_LOCATION
    return file_path.replace("\\", "/")


def _enum_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value
