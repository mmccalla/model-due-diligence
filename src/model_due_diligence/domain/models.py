"""Domain models for model-due-diligence.

This module contains shared immutable value objects used across the CLI,
scanners, external tool adapters, risk scoring and reporting layers.

Keep this module free of filesystem access, subprocess calls and reporting
logic. It is the common language of the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    """Normalised severity for scanner findings."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, Enum):
    """Overall risk level assigned to a scan report."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FileCategory(str, Enum):
    """Normalised file categories used by inventory and reports."""

    COMPILED_BINARY = "compiled_binary"
    DEPENDENCY_OR_BUILD_FILE = "dependency_or_build_file"
    HIGH_RISK_SERIALISED_MODEL = "high_risk_serialised_model"
    LOWER_RISK_MODEL_FORMAT = "lower_risk_model_format"
    OTHER = "other"
    SCRIPT_OR_EXECUTABLE = "script_or_executable"
    SYMLINK = "symlink"
    UNREADABLE = "unreadable"


class ReportFormat(str, Enum):
    """Supported report output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    SARIF = "sarif"


@dataclass(frozen=True, slots=True)
class Finding:
    """A normalised scanner finding.

    A finding is review evidence, not proof of compromise. Scanners should use
    this type rather than returning tool-specific dictionaries.
    """

    severity: Severity
    category: str
    file: str
    message: str
    evidence: str | None = None
    recommendation: str | None = None
    scanner: str | None = None


@dataclass(frozen=True, slots=True)
class FileRecord:
    """Inventory record for a scanned file or symlink."""

    path: str
    absolute_path: str
    size_bytes: int
    sha256: str
    extension: str
    category: FileCategory | str
    is_symlink: bool
    symlink_target: str | None
    mode_octal: str
    executable: bool


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Result from an external scanner or quality tool invocation."""

    tool: str
    available: bool
    command: list[str]
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    output_files: list[str] = field(default_factory=list)
    duration_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Static metadata extracted from a model artefact."""

    file: str
    kind: str
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AuditSummary:
    """Stable summary values for human and machine-readable reports."""

    files_scanned: int
    findings: int
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    info_findings: int = 0
    external_tools_run: int = 0
    file_categories: dict[str, int] = field(default_factory=dict)
    git: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AuditReport:
    """Complete scan report model used by report renderers."""

    scanned_path: str
    generated_at_utc: str
    files: list[FileRecord]
    metadata: list[ModelMetadata]
    findings: list[Finding]
    tools: list[CommandResult]
    risk_score: int
    risk_level: RiskLevel
    summary: AuditSummary | dict[str, Any]


@dataclass(frozen=True, slots=True)
class ScanContext:
    """Runtime scan configuration built by the CLI and passed to the app layer."""

    target: Path
    root: Path
    output_dir: Path
    timeout_seconds: int
    fail_on: RiskLevel = RiskLevel.HIGH
    report_formats: tuple[ReportFormat, ...] = (ReportFormat.MARKDOWN, ReportFormat.JSON)
    skip_external: bool = False
    skip_semgrep: bool = False
    skip_bandit: bool = False
    skip_pip_audit: bool = False
    skip_detect_secrets: bool = False
    skip_modelscan: bool = False
    skip_quality_self_check: bool = False
    quality_self_check: bool = False


@dataclass(frozen=True, slots=True)
class ScannerResult:
    """Normalised result returned by a native scanner."""

    scanner: str
    findings: list[Finding] = field(default_factory=list)
    metadata: list[ModelMetadata] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ExternalScannerResult:
    """Normalised result returned by an external scanner adapter."""

    tool_result: CommandResult
    findings: list[Finding] = field(default_factory=list)
