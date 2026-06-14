"""Scan orchestration for the mdd-ui API layer."""

from __future__ import annotations

import dataclasses
import tempfile
from collections.abc import Callable
from dataclasses import asdict, is_dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, cast

from model_due_diligence.app import ModelDueDiligenceApp
from model_due_diligence.domain.models import AuditReport, ReportFormat, ScanContext
from model_due_diligence.ollama import resolve_installed_model, stage_model_for_scan
from model_due_diligence.reporting.json_report import write_json_report_to_directory
from model_due_diligence.reporting.markdown_report import write_markdown_report_to_directory
from model_due_diligence.reporting.sarif_report import write_sarif_report_to_directory
from model_due_diligence.ui.schemas import (
    InteractionState,
    ScanPreviewItem,
    ScanPreviewResponse,
    ScanReportPaths,
    ScanResponse,
    ScanTargetRequest,
    ScanTargetType,
)

RunScanFn = Callable[[ScanContext], AuditReport]


@dataclasses.dataclass(frozen=True, slots=True)
class PreparedScan:
    """Scan context plus optional temporary staging directory."""

    context: ScanContext
    scanned_path_label: str
    temp_dir: tempfile.TemporaryDirectory[str] | None


def prepare_scan(request: ScanTargetRequest, output_dir: Path) -> PreparedScan:
    """Build a scan context for a UI request."""

    options = request.options
    if request.target_type == ScanTargetType.OLLAMA:
        model_name = request.target.strip()
        staged_path, temp_dir = _stage_ollama_target(model_name)
        context = ScanContext(
            target=staged_path,
            root=staged_path,
            output_dir=output_dir,
            timeout_seconds=options.timeout_seconds,
            fail_on=options.fail_on,
            report_formats=(ReportFormat.MARKDOWN, ReportFormat.JSON, ReportFormat.SARIF),
            skip_external=options.skip_external,
            skip_semgrep=options.skip_semgrep,
            skip_bandit=options.skip_bandit,
            skip_pip_audit=options.skip_pip_audit,
            skip_detect_secrets=options.skip_detect_secrets,
            skip_modelscan=options.skip_modelscan,
        )
        return PreparedScan(context=context, scanned_path_label=f"ollama:{model_name}", temp_dir=temp_dir)

    target = Path(request.target.strip()).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target does not exist: {target}")

    root = target if target.is_dir() else target.parent
    context = ScanContext(
        target=target,
        root=root,
        output_dir=output_dir,
        timeout_seconds=options.timeout_seconds,
        fail_on=options.fail_on,
        report_formats=(ReportFormat.MARKDOWN, ReportFormat.JSON, ReportFormat.SARIF),
        skip_external=options.skip_external,
        skip_semgrep=options.skip_semgrep,
        skip_bandit=options.skip_bandit,
        skip_pip_audit=options.skip_pip_audit,
        skip_detect_secrets=options.skip_detect_secrets,
        skip_modelscan=options.skip_modelscan,
    )
    return PreparedScan(context=context, scanned_path_label=str(target), temp_dir=None)


def preview_scan(request: ScanTargetRequest) -> ScanPreviewResponse:
    """Return a plan preview without running scanners."""

    target = request.target.strip()
    if request.target_type == ScanTargetType.OLLAMA:
        return _preview_ollama_target(target)
    return _preview_path_target(target)


def run_scan(
    request: ScanTargetRequest,
    output_dir: Path,
    *,
    app: ModelDueDiligenceApp | None = None,
    runner: RunScanFn | None = None,
) -> ScanResponse:
    """Run a static scan and return a serialised report payload."""

    prepared = prepare_scan(request, output_dir)
    try:
        report = (runner or (app or ModelDueDiligenceApp()).run)(prepared.context)
        report = replace(report, scanned_path=prepared.scanned_path_label)
        markdown_path = write_markdown_report_to_directory(report, output_dir)
        json_path = write_json_report_to_directory(report, output_dir)
        sarif_path = write_sarif_report_to_directory(report, output_dir)
    finally:
        if prepared.temp_dir is not None:
            prepared.temp_dir.cleanup()

    warnings: list[str] = []
    if request.options.skip_external:
        warnings.append("External scanners were skipped for this run.")

    return ScanResponse(
        state=InteractionState.SUCCESS,
        target_type=request.target_type,
        target=request.target.strip(),
        scanned_path=report.scanned_path,
        report=serialise_audit_report(report),
        report_paths=ScanReportPaths(
            markdown_path=str(markdown_path),
            json_path=str(json_path),
            sarif_path=str(sarif_path),
            output_dir=str(output_dir),
        ),
        warnings=warnings,
        message="Static scan completed. Review findings before loading the model.",
    )


def serialise_audit_report(report: AuditReport) -> dict[str, object]:
    """Convert an audit report dataclass graph into JSON-serialisable data."""

    return _serialise_value(report)


def _preview_ollama_target(model_name: str) -> ScanPreviewResponse:
    resolved = resolve_installed_model(model_name)
    staged_path, temp_dir = stage_model_for_scan(resolved)
    try:
        items = _preview_items_for_directory(staged_path)
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()

    return ScanPreviewResponse(
        state=InteractionState.SUCCESS,
        target_type=ScanTargetType.OLLAMA,
        target=model_name,
        resolved_path=str(staged_path),
        items=items,
        warnings=[
            "Static inspection only. No model weights will be loaded and no inference will run.",
        ],
        message=f"Ready to inspect staged artefacts for Ollama model {model_name!r}.",
    )


def _preview_path_target(raw_target: str) -> ScanPreviewResponse:
    target = Path(raw_target).expanduser().resolve()
    if not target.exists():
        return ScanPreviewResponse(
            state=InteractionState.ERROR,
            target_type=ScanTargetType.PATH,
            target=raw_target,
            message=f"Target does not exist: {target}",
        )

    if target.is_file():
        items = [_preview_item_for_file(target)]
        message = f"Ready to inspect file {target.name!r}."
    else:
        items = _preview_items_for_directory(target, limit=25)
        message = f"Ready to inspect directory {target}."

    return ScanPreviewResponse(
        state=InteractionState.SUCCESS,
        target_type=ScanTargetType.PATH,
        target=raw_target,
        resolved_path=str(target),
        items=items,
        warnings=[
            "Static inspection only. No model weights will be loaded and no inference will run.",
        ],
        message=message,
    )


def _stage_ollama_target(model_name: str) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    resolved = resolve_installed_model(model_name)
    return stage_model_for_scan(resolved)


def _preview_items_for_directory(directory: Path, *, limit: int = 50) -> list[ScanPreviewItem]:
    items: list[ScanPreviewItem] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        items.append(_preview_item_for_file(path, root=directory))
        if len(items) >= limit:
            break
    return items


def _preview_item_for_file(path: Path, *, root: Path | None = None) -> ScanPreviewItem:
    display_root = root or path.parent
    try:
        label = str(path.relative_to(display_root))
    except ValueError:
        label = path.name
    return ScanPreviewItem(
        label=label,
        path=str(path),
        kind=_file_kind(path),
        size_bytes=_safe_size(path),
    )


def _file_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".gguf":
        return "gguf"
    if suffix == ".safetensors":
        return "safetensors"
    if suffix in {".json", ".txt", ".md"}:
        return "metadata"
    return "file"


def _safe_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def _serialise_value(value: object) -> dict[str, object]:
    if is_dataclass(value) and not isinstance(value, type):
        payload = asdict(cast(Any, value))
        return {key: _serialise_nested(item) for key, item in payload.items()}
    if isinstance(value, dict):
        return {str(key): _serialise_nested(item) for key, item in value.items()}
    raise TypeError(f"Unsupported report payload type: {type(value)!r}")


def _serialise_nested(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _serialise_nested(item) for key, item in asdict(cast(Any, value)).items()}
    if isinstance(value, list):
        return [_serialise_nested(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialise_nested(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value
