"""File inventory builder.

This module creates the static file inventory used by the rest of the scan. It
classifies artefacts, records hashes, captures symlink and permission metadata,
and emits conservative findings for artefacts that require review.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from model_due_diligence.config.defaults import (
    COMPILED_BINARY_EXTENSIONS,
    DEPENDENCY_FILE_NAMES,
    EXECUTABLE_OR_SCRIPT_EXTENSIONS,
    HIGH_RISK_SERIALISATION_EXTENSIONS,
    LOWER_RISK_MODEL_EXTENSIONS,
)
from model_due_diligence.domain.models import FileCategory, FileRecord, Finding, ScanContext, Severity
from model_due_diligence.utils import iter_files, safe_relative, sha256_file


def classify_file(path: Path) -> FileCategory:
    """Return the normalised category for a file path."""

    suffix = path.suffix.lower()
    name = path.name.lower()

    if path.is_symlink():
        return FileCategory.SYMLINK

    suffix_categories = (
        (HIGH_RISK_SERIALISATION_EXTENSIONS, FileCategory.HIGH_RISK_SERIALISED_MODEL),
        (LOWER_RISK_MODEL_EXTENSIONS, FileCategory.LOWER_RISK_MODEL_FORMAT),
        (COMPILED_BINARY_EXTENSIONS, FileCategory.COMPILED_BINARY),
        (EXECUTABLE_OR_SCRIPT_EXTENSIONS, FileCategory.SCRIPT_OR_EXECUTABLE),
    )
    for extensions, category in suffix_categories:
        if suffix in extensions:
            return category

    if name in DEPENDENCY_FILE_NAMES or name in {"setup.py", "setup.cfg"}:
        return FileCategory.DEPENDENCY_OR_BUILD_FILE

    return FileCategory.OTHER


def is_executable(path: Path) -> bool:
    """Return true when any executable permission bit is set."""

    try:
        mode = path.lstat().st_mode
    except OSError:
        return False

    return bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


class FileInventoryBuilder:
    """Build file inventory records and file-level findings."""

    scanner_name = "file_inventory"

    def build(self, context: ScanContext) -> tuple[list[FileRecord], list[Finding]]:
        """Build inventory records for all files under the scan target."""

        records: list[FileRecord] = []
        findings: list[Finding] = []

        for path in iter_files(context.target):
            relative = safe_relative(path, context.root)

            try:
                record = self._build_record(path, relative)
            except OSError as exc:
                findings.append(self._file_read_error(relative, exc))
                continue

            records.append(record)
            findings.extend(self._find_file_risks(record))

        return records, findings

    def _build_record(self, path: Path, relative: str) -> FileRecord:
        stat_result = path.lstat()
        is_link = path.is_symlink()

        return FileRecord(
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

    def _file_read_error(self, relative: str, exc: OSError) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="file_read_error",
            file=relative,
            message=f"Could not read file metadata: {exc}",
            recommendation="Review filesystem permissions and rerun the scan.",
            scanner=self.scanner_name,
        )

    def _find_file_risks(self, record: FileRecord) -> list[Finding]:
        findings: list[Finding] = []

        if record.is_symlink:
            findings.append(self._symlink_finding(record))

        if record.extension in HIGH_RISK_SERIALISATION_EXTENSIONS:
            findings.append(self._high_risk_serialisation_finding(record))

        if record.extension in LOWER_RISK_MODEL_EXTENSIONS:
            findings.append(self._lower_risk_model_format_finding(record))

        if record.category == FileCategory.COMPILED_BINARY:
            findings.append(self._compiled_binary_finding(record))

        if record.category == FileCategory.SCRIPT_OR_EXECUTABLE:
            findings.append(self._script_or_executable_finding(record))

        if record.executable and record.category not in {
            FileCategory.SCRIPT_OR_EXECUTABLE,
            FileCategory.COMPILED_BINARY,
        }:
            findings.append(self._executable_permission_finding(record))

        return findings

    def _symlink_finding(self, record: FileRecord) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="symlink",
            file=record.path,
            message=f"Symlink detected, target={record.symlink_target!r}.",
            recommendation="Verify the link does not point outside the expected model directory.",
            scanner=self.scanner_name,
        )

    def _high_risk_serialisation_finding(self, record: FileRecord) -> Finding:
        return Finding(
            severity=Severity.HIGH,
            category="unsafe_or_high_risk_serialisation",
            file=record.path,
            message=f"High-risk serialisation format detected: {record.extension}.",
            recommendation=(
                "Prefer safetensors, GGUF or ONNX. Do not load this artefact unless provenance is trusted "
                "and scanner findings are understood."
            ),
            scanner=self.scanner_name,
        )

    def _lower_risk_model_format_finding(self, record: FileRecord) -> Finding:
        return Finding(
            severity=Severity.INFO,
            category="lower_risk_model_format",
            file=record.path,
            message=f"Lower-risk model format detected: {record.extension}.",
            recommendation="Still verify provenance, hash and first-run sandboxing.",
            scanner=self.scanner_name,
        )

    def _compiled_binary_finding(self, record: FileRecord) -> Finding:
        return Finding(
            severity=Severity.HIGH,
            category="compiled_binary",
            file=record.path,
            message="Compiled binary present in model artefact.",
            recommendation="Treat as executable code. Review origin and avoid loading in a privileged environment.",
            scanner=self.scanner_name,
        )

    def _script_or_executable_finding(self, record: FileRecord) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="script_or_executable",
            file=record.path,
            message="Script or executable file present.",
            recommendation="Review manually before running or importing the repository.",
            scanner=self.scanner_name,
        )

    def _executable_permission_finding(self, record: FileRecord) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="executable_permission",
            file=record.path,
            message=f"Executable permission bit set: {record.mode_octal}.",
            recommendation="Check whether executable permissions are expected for this artefact.",
            scanner=self.scanner_name,
        )
