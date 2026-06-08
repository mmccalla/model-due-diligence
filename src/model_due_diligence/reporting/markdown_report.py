"""Markdown report renderer.

The Markdown report is the primary human-readable output for reviewers. It
should be clear, conservative and explicit that static scanning provides review
evidence rather than proof of model safety.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from model_due_diligence.config.defaults import REPORT_MARKDOWN_FILENAME
from model_due_diligence.domain.models import AuditReport, AuditSummary, FileCategory, Severity


SEVERITY_SORT_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

MAX_METADATA_CHARS = 5_000
MAX_TOOL_OUTPUT_CHARS = 5_000


def write_markdown_report(report: AuditReport, path: Path) -> None:
    """Write a Markdown report to a specific path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")


def write_markdown_report_to_directory(report: AuditReport, output_dir: Path) -> Path:
    """Write the standard Markdown report into an output directory."""

    output_path = output_dir / REPORT_MARKDOWN_FILENAME
    write_markdown_report(report, output_path)
    return output_path


def render_markdown(report: AuditReport) -> str:
    """Render a complete audit report as Markdown."""

    lines: list[str] = []

    _append_header(lines, report)
    _append_summary(lines, report)
    _append_findings(lines, report)
    _append_model_metadata(lines, report)
    _append_external_tool_results(lines, report)
    _append_file_inventory(lines, report)
    _append_interpretation(lines)

    return "\n".join(lines)


def _append_header(lines: list[str], report: AuditReport) -> None:
    lines.extend(
        [
            "# Model Due Diligence Report",
            "",
            f"**Scanned path:** `{_escape_inline(report.scanned_path)}`",
            f"**Generated UTC:** `{_escape_inline(report.generated_at_utc)}`",
            f"**Risk level:** **{report.risk_level.value}**",
            f"**Risk score:** `{report.risk_score}/100`",
            "",
        ]
    )


def _append_summary(lines: list[str], report: AuditReport) -> None:
    lines.extend(["## Summary", ""])

    summary = _summary_as_dict(report.summary)
    if not summary:
        lines.append("No summary values generated.")
        lines.append("")
        return

    for key, value in summary.items():
        lines.append(f"- **{_humanise_key(key)}:** `{_escape_inline(_format_value(value))}`")

    lines.append("")


def _append_findings(lines: list[str], report: AuditReport) -> None:
    lines.extend(["## Findings", ""])

    if not report.findings:
        lines.extend(["No findings generated.", ""])
        return

    lines.extend(
        [
            "| Severity | Scanner | Category | File | Message | Evidence | Recommendation |",
            "|---|---|---|---|---|---|---|",
        ]
    )

    for finding in sorted(
        report.findings,
        key=lambda item: (SEVERITY_SORT_ORDER[item.severity], item.scanner or "", item.file, item.category),
    ):
        lines.append(
            "| "
            f"{finding.severity.value} | "
            f"`{_escape_table(finding.scanner or '')}` | "
            f"`{_escape_table(finding.category)}` | "
            f"`{_escape_table(finding.file)}` | "
            f"{_escape_table(finding.message)} | "
            f"{_escape_table(finding.evidence or '')} | "
            f"{_escape_table(finding.recommendation or '')} |"
        )

    lines.append("")


def _append_model_metadata(lines: list[str], report: AuditReport) -> None:
    lines.extend(["## Model Metadata", ""])

    if not report.metadata:
        lines.extend(["No GGUF or safetensors metadata extracted.", ""])
        return

    for item in report.metadata:
        lines.extend(
            [
                f"### `{_escape_inline(item.file)}`",
                "",
                f"- Kind: `{_escape_inline(item.kind)}`",
            ]
        )

        if item.warnings:
            lines.append(f"- Warnings: `{_escape_inline(_format_value(item.warnings))}`")

        lines.extend(
            [
                "",
                "```json",
                _truncate(json.dumps(item.metadata, indent=2, ensure_ascii=False), MAX_METADATA_CHARS),
                "```",
                "",
            ]
        )


def _append_external_tool_results(lines: list[str], report: AuditReport) -> None:
    lines.extend(["## External Tool Results", ""])

    if not report.tools:
        lines.extend(["No external tools were run.", ""])
        return

    for tool in report.tools:
        lines.extend(
            [
                f"### `{_escape_inline(tool.tool)}`",
                "",
                f"- Available: `{tool.available}`",
                f"- Exit code: `{tool.exit_code}`",
                f"- Duration seconds: `{tool.duration_seconds}`",
                f"- Command: `{_escape_inline(' '.join(tool.command))}`",
            ]
        )

        if tool.output_files:
            lines.append(f"- Output files: `{_escape_inline(_format_value(tool.output_files))}`")

        _append_tool_stream(lines, "stdout", tool.stdout)
        _append_tool_stream(lines, "stderr", tool.stderr)

        lines.append("")


def _append_file_inventory(lines: list[str], report: AuditReport) -> None:
    lines.extend(
        [
            "## File Inventory",
            "",
            "| Category | Extension | Executable | Size | SHA-256 | Path |",
            "|---|---:|---:|---:|---|---|",
        ]
    )

    for record in report.files:
        lines.append(
            "| "
            f"`{_escape_table(_file_category_value(record.category))}` | "
            f"`{_escape_table(record.extension)}` | "
            f"`{record.executable}` | "
            f"{record.size_bytes} | "
            f"`{_escape_table(record.sha256)}` | "
            f"`{_escape_table(record.path)}` |"
        )

    lines.append("")


def _append_interpretation(lines: list[str]) -> None:
    lines.extend(
        [
            "## Interpretation",
            "",
            "A LOW result does not prove that a model is safe. It means only that this static due-diligence pass did not identify the supported static artefact risks it is designed to detect.",
            "",
            "Before loading or importing any model artefact, use the broader control pattern:",
            "",
            "```text",
            "Official or reputable source",
            "+ pinned commit or hash",
            "+ static due-diligence scan",
            "+ first run in a no-network sandbox",
            "+ no credentials mounted",
            "+ restricted filesystem access",
            "+ adversarial behavioural test suite",
            "+ runtime monitoring",
            "+ human review",
            "= reasonable practical risk reduction",
            "```",
            "",
            "## Known Limitations",
            "",
            "Static scanning cannot reliably detect:",
            "",
            "- malicious behaviour encoded directly into model weights;",
            "- sleeper-agent or trigger-based backdoors;",
            "- training-data poisoning;",
            "- all unsafe deserialisation evasions;",
            "- prompt-injection obedience in downstream RAG or agent workflows;",
            "- data exfiltration behaviour that only appears during runtime.",
            "",
            "Use generated reports as review evidence, not as an automated trust verdict.",
        ]
    )


def _append_tool_stream(lines: list[str], stream_name: str, value: str) -> None:
    if not value.strip():
        return

    lines.extend(
        [
            "",
            f"**{stream_name}:**",
            "",
            "```text",
            _truncate(value.strip(), MAX_TOOL_OUTPUT_CHARS),
            "```",
        ]
    )


def _summary_as_dict(summary: AuditSummary | dict[str, Any]) -> dict[str, Any]:
    if isinstance(summary, AuditSummary):
        return {
            "files_scanned": summary.files_scanned,
            "findings": summary.findings,
            "critical_findings": summary.critical_findings,
            "high_findings": summary.high_findings,
            "medium_findings": summary.medium_findings,
            "low_findings": summary.low_findings,
            "info_findings": summary.info_findings,
            "external_tools_run": summary.external_tools_run,
            "file_categories": summary.file_categories,
            "git": summary.git,
        }

    return dict(summary)


def _file_category_value(category: FileCategory | str) -> str:
    if isinstance(category, FileCategory):
        return category.value
    return category


def _humanise_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _format_value(value: Any) -> str:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n...[truncated]..."


def _escape_inline(value: str) -> str:
    return value.replace("`", "\\`")


def _escape_table(value: str) -> str:
    return _escape_inline(value).replace("|", "\\|").replace("\n", "<br>")
