"""Unit tests for the file inventory builder."""

from __future__ import annotations

import os
from pathlib import Path

from model_due_diligence.domain.models import FileCategory, RiskLevel, ScanContext, Severity
from model_due_diligence.inventory.file_inventory import FileInventoryBuilder, classify_file, is_executable


def _context(target: Path, output_dir: Path) -> ScanContext:
    return ScanContext(
        target=target,
        root=target if target.is_dir() else target.parent,
        output_dir=output_dir,
        timeout_seconds=10,
        fail_on=RiskLevel.HIGH,
    )


def test_inventory_builds_hash_for_regular_file(tmp_path: Path) -> None:
    target = tmp_path / "model.gguf"
    target.write_bytes(b"GGUF" + b"\x03\x00\x00\x00")

    records, findings = FileInventoryBuilder().build(_context(target, tmp_path / "out"))

    assert len(records) == 1
    assert records[0].sha256 != ""
    assert records[0].sha256 != "SYMLINK"
    assert records[0].category == FileCategory.LOWER_RISK_MODEL_FORMAT
    assert any(finding.category == "lower_risk_model_format" for finding in findings)


def test_inventory_classifies_high_risk_serialisation(tmp_path: Path) -> None:
    target = tmp_path / "weights.pkl"
    target.write_bytes(b"pickle-like content")

    records, findings = FileInventoryBuilder().build(_context(target, tmp_path / "out"))

    assert records[0].category == FileCategory.HIGH_RISK_SERIALISED_MODEL
    assert any(
        finding.category == "unsafe_or_high_risk_serialisation" and finding.severity == Severity.HIGH
        for finding in findings
    )


def test_inventory_records_symlink_without_hashing_target(tmp_path: Path) -> None:
    real_file = tmp_path / "real.txt"
    real_file.write_text("safe fixture\n", encoding="utf-8")
    symlink = tmp_path / "link.txt"
    symlink.symlink_to(real_file)

    records, findings = FileInventoryBuilder().build(_context(symlink, tmp_path / "out"))

    assert len(records) == 1
    assert records[0].is_symlink is True
    assert records[0].sha256 == "SYMLINK"
    assert records[0].category == FileCategory.SYMLINK
    assert records[0].symlink_target == str(real_file)
    assert any(finding.category == "symlink" for finding in findings)


def test_inventory_flags_compiled_binary(tmp_path: Path) -> None:
    target = tmp_path / "extension.so"
    target.write_bytes(b"binary-like content")

    records, findings = FileInventoryBuilder().build(_context(target, tmp_path / "out"))

    assert records[0].category == FileCategory.COMPILED_BINARY
    assert any(finding.category == "compiled_binary" and finding.severity == Severity.HIGH for finding in findings)


def test_inventory_flags_script_or_executable_extension(tmp_path: Path) -> None:
    target = tmp_path / "setup.sh"
    target.write_text("#!/usr/bin/env bash\necho hello\n", encoding="utf-8")

    records, findings = FileInventoryBuilder().build(_context(target, tmp_path / "out"))

    assert records[0].category == FileCategory.SCRIPT_OR_EXECUTABLE
    assert any(finding.category == "script_or_executable" for finding in findings)


def test_inventory_flags_unexpected_executable_permission(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("hello\n", encoding="utf-8")
    target.chmod(0o755)

    records, findings = FileInventoryBuilder().build(_context(target, tmp_path / "out"))

    assert records[0].executable is True
    assert any(finding.category == "executable_permission" for finding in findings)


def test_classify_file_detects_dependency_file(tmp_path: Path) -> None:
    target = tmp_path / "requirements.txt"
    target.write_text("requests==2.31.0\n", encoding="utf-8")

    assert classify_file(target) == FileCategory.DEPENDENCY_OR_BUILD_FILE


def test_is_executable_returns_false_for_missing_file(tmp_path: Path) -> None:
    assert is_executable(tmp_path / "missing") is False


def test_is_executable_returns_true_when_execute_bit_set(tmp_path: Path) -> None:
    target = tmp_path / "tool"
    target.write_text("hello\n", encoding="utf-8")
    target.chmod(target.stat().st_mode | os.stat_result((0o111,) * 10).st_mode)

    assert is_executable(target) is True
