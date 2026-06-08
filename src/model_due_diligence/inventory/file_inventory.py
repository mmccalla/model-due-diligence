from __future__ import annotations

import os
import stat
from pathlib import Path

from model_due_diligence.config.defaults import EXECUTABLE_OR_SCRIPT_EXTENSIONS, HIGH_RISK_SERIALISATION_EXTENSIONS, LOWER_RISK_MODEL_EXTENSIONS
from model_due_diligence.domain.models import FileRecord, Finding, ScanContext, Severity
from model_due_diligence.utils import iter_files, safe_relative, sha256_file


def classify_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if path.is_symlink():
        return "symlink"
    if suffix in HIGH_RISK_SERIALISATION_EXTENSIONS:
        return "high_risk_serialised_model"
    if suffix in LOWER_RISK_MODEL_EXTENSIONS:
        return "lower_risk_model_format"
    if suffix in {".so", ".dylib", ".dll", ".exe"}:
        return "compiled_binary"
    if suffix in EXECUTABLE_OR_SCRIPT_EXTENSIONS:
        return "script_or_executable"
    if path.name.lower() in {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"}:
        return "dependency_or_build_file"
    return "other"


def is_executable(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
        return bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    except OSError:
        return False


class FileInventoryBuilder:
    def build(self, context: ScanContext) -> tuple[list[FileRecord], list[Finding]]:
        records: list[FileRecord] = []
        findings: list[Finding] = []
        for path in iter_files(context.target):
            relative = safe_relative(path, context.root)
            try:
                stat_result = path.lstat()
                is_link = path.is_symlink()
                record = FileRecord(
                    path=relative,
                    absolute_path=str(path),
                    size_bytes=stat_result.st_size,
                    sha256="SYMLINK" if is_link else sha256_file(path),
                    extension=path.suffix.lower(),
                    category=classify_file(path),
                    is_symlink=is_link,
                    symlink_target=os.readlink(path) if is_link else None,
                    mode_octal=oct(stat_result.st_mode & 0o777),
                    executable=is_executable(path),
                )
                records.append(record)
                findings.extend(self._find_file_risks(record))
            except OSError as exc:
                findings.append(Finding(Severity.MEDIUM, "file_read_error", relative, f"Could not read file metadata: {exc}"))
        return records, findings

    @staticmethod
    def _find_file_risks(record: FileRecord) -> list[Finding]:
        findings: list[Finding] = []
        if record.is_symlink:
            findings.append(Finding(Severity.MEDIUM, "symlink", record.path, f"Symlink detected, target={record.symlink_target!r}", recommendation="Verify the link does not point outside the expected model directory."))
        if record.extension in HIGH_RISK_SERIALISATION_EXTENSIONS:
            findings.append(Finding(Severity.HIGH, "unsafe_or_high_risk_serialisation", record.path, f"High-risk serialisation format detected: {record.extension}", recommendation="Prefer safetensors/GGUF/ONNX; do not load unless provenance is trusted."))
        if record.extension in LOWER_RISK_MODEL_EXTENSIONS:
            findings.append(Finding(Severity.INFO, "lower_risk_model_format", record.path, f"Lower-risk model format detected: {record.extension}.", recommendation="Still verify provenance, hash and first-run sandboxing."))
        if record.category == "compiled_binary":
            findings.append(Finding(Severity.HIGH, "compiled_binary", record.path, "Compiled binary present in model artefact."))
        if record.category == "script_or_executable":
            findings.append(Finding(Severity.MEDIUM, "script_or_executable", record.path, "Script or executable file present."))
        return findings
