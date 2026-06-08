from __future__ import annotations

import json
from model_due_diligence.domain.models import AuditReport, Severity


def render_markdown(report: AuditReport) -> str:
    lines: list[str] = ["# Model Due Diligence Report", "", f"**Scanned path:** `{report.scanned_path}`", f"**Generated UTC:** `{report.generated_at_utc}`", f"**Risk level:** **{report.risk_level.value}**", f"**Risk score:** `{report.risk_score}/100`", "", "## Summary", ""]
    for key, value in report.summary.items():
        lines.append(f"- **{key}:** `{value}`")
    lines.extend(["", "## Findings", ""])
    if report.findings:
        lines.extend(["| Severity | Category | File | Message | Recommendation |", "|---|---|---|---|---|"])
        ordered = sorted(report.findings, key=lambda f: ({Severity.CRITICAL:0, Severity.HIGH:1, Severity.MEDIUM:2, Severity.LOW:3, Severity.INFO:4}[f.severity], f.file, f.category))
        for f in ordered:
            lines.append(f"| {f.severity.value} | `{f.category}` | `{f.file}` | {f.message} | {f.recommendation or ''} |")
    else:
        lines.append("No findings generated.")
    lines.extend(["", "## Model Metadata", ""])
    if report.metadata:
        for item in report.metadata:
            lines.extend([f"### `{item.file}`", "", f"- Kind: `{item.kind}`", "", "```json", json.dumps(item.metadata, indent=2, ensure_ascii=False)[:5000], "```", ""])
    else:
        lines.append("No GGUF or safetensors metadata extracted.")
    lines.extend(["", "## External Tool Results", ""])
    for t in report.tools:
        lines.extend([f"### `{t.tool}`", "", f"- Available: `{t.available}`", f"- Exit code: `{t.exit_code}`", f"- Command: `{' '.join(t.command)}`", ""])
    lines.extend(["## File Inventory", "", "| Category | Extension | Executable | Size | SHA-256 | Path |", "|---|---:|---:|---:|---|---|"])
    for r in report.files:
        lines.append(f"| `{r.category}` | `{r.extension}` | `{r.executable}` | {r.size_bytes} | `{r.sha256}` | `{r.path}` |")
    lines.extend(["", "## Interpretation", "", "A LOW result does not prove that the model is safe. Do not load untrusted models with credentials, network access, or write access to sensitive directories."])
    return "\n".join(lines)
