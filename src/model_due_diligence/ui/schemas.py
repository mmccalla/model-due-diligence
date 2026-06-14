"""API schemas for the mdd-ui local dashboard.

These models encode interaction states explicitly so the frontend can render
predictable loading, empty, partial-success and error surfaces without
inferring status from missing fields.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from model_due_diligence.domain.models import RiskLevel


class InteractionState(StrEnum):
    """Frontend-visible interaction state for a UI surface."""

    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    EMPTY = "empty"
    WARNING = "warning"
    ERROR = "error"
    RUNNING = "running"


class OllamaDiscoverySource(StrEnum):
    """Where installed Ollama model metadata was discovered."""

    API = "api"
    FILESYSTEM = "filesystem"
    NONE = "none"


class ScanTargetType(StrEnum):
    """Supported scan target kinds for the UI."""

    OLLAMA = "ollama"
    PATH = "path"


class HealthResponse(BaseModel):
    """API health and version information."""

    status: Literal["ok"] = "ok"
    version: str
    service: Literal["mdd-ui"] = "mdd-ui"


class OllamaStatusResponse(BaseModel):
    """Ollama server connectivity and discovery mode."""

    state: InteractionState
    source: OllamaDiscoverySource
    host: str
    connected: bool
    message: str


class OllamaModelSummary(BaseModel):
    """Summary of one installed Ollama model."""

    name: str
    source: OllamaDiscoverySource
    size_bytes: int | None = None
    modified_at: str | None = None
    family: str | None = None
    digest: str | None = None


class OllamaModelsResponse(BaseModel):
    """Installed Ollama models from API and/or local store."""

    state: InteractionState
    source: OllamaDiscoverySource
    host: str
    models: list[OllamaModelSummary] = Field(default_factory=list)
    message: str


class ScanOptions(BaseModel):
    """Scan configuration exposed to the UI."""

    skip_external: bool = True
    skip_semgrep: bool = False
    skip_bandit: bool = False
    skip_pip_audit: bool = False
    skip_detect_secrets: bool = False
    skip_modelscan: bool = False
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    fail_on: RiskLevel = RiskLevel.HIGH


class ScanTargetRequest(BaseModel):
    """Scan or preview request payload."""

    target_type: ScanTargetType
    target: str = Field(min_length=1)
    options: ScanOptions = Field(default_factory=ScanOptions)


class ScanPreviewItem(BaseModel):
    """One artefact that a scan will inspect."""

    label: str
    path: str
    kind: str
    size_bytes: int | None = None


class ScanPreviewResponse(BaseModel):
    """Plan preview shown before running a static scan."""

    state: InteractionState
    target_type: ScanTargetType
    target: str
    resolved_path: str | None = None
    items: list[ScanPreviewItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    message: str


class ScanReportPaths(BaseModel):
    """Filesystem paths for generated report artefacts."""

    markdown_path: str | None = None
    json_path: str | None = None
    sarif_path: str | None = None
    output_dir: str


class ScanResponse(BaseModel):
    """Completed scan response for the report panel."""

    state: InteractionState
    target_type: ScanTargetType
    target: str
    scanned_path: str
    report: dict[str, Any]
    report_paths: ScanReportPaths
    warnings: list[str] = Field(default_factory=list)
    message: str


class ErrorResponse(BaseModel):
    """Structured client or validation error."""

    state: InteractionState = InteractionState.ERROR
    error: str
    detail: str | None = None
