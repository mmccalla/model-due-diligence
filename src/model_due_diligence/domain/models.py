from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    category: str
    file: str
    message: str
    evidence: str | None = None
    recommendation: str | None = None


@dataclass(frozen=True)
class FileRecord:
    path: str
    absolute_path: str
    size_bytes: int
    sha256: str
    extension: str
    category: str
    is_symlink: bool
    symlink_target: str | None
    mode_octal: str
    executable: bool


@dataclass(frozen=True)
class CommandResult:
    tool: str
    available: bool
    command: list[str]
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    output_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ModelMetadata:
    file: str
    kind: str
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditReport:
    scanned_path: str
    generated_at_utc: str
    files: list[FileRecord]
    metadata: list[ModelMetadata]
    findings: list[Finding]
    tools: list[CommandResult]
    risk_score: int
    risk_level: RiskLevel
    summary: dict[str, Any]


@dataclass(frozen=True)
class ScanContext:
    target: Path
    root: Path
    output_dir: Path
    timeout_seconds: int
    skip_external: bool = False
    skip_semgrep: bool = False
    skip_bandit: bool = False
    skip_pip_audit: bool = False
    skip_detect_secrets: bool = False
    skip_modelscan: bool = False
    skip_quality_self_check: bool = False
    quality_self_check: bool = False
