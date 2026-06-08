"""Unit tests for the model metadata scanner."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from model_due_diligence.domain.models import RiskLevel, ScanContext, Severity
from model_due_diligence.scanners.model_metadata import ModelMetadataScanner


def _context(target: Path, output_dir: Path) -> ScanContext:
    return ScanContext(
        target=target,
        root=target if target.is_dir() else target.parent,
        output_dir=output_dir,
        timeout_seconds=10,
        fail_on=RiskLevel.HIGH,
    )


def _safetensors_bytes(header: dict[str, object]) -> bytes:
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    return struct.pack("<Q", len(header_bytes)) + header_bytes


def test_gguf_metadata_extracts_magic_version_and_size(tmp_path: Path) -> None:
    target = tmp_path / "x.gguf"
    target.write_bytes(b"GGUF" + b"\x03\x00\x00\x00" + (b"0" * 32))

    metadata, findings = ModelMetadataScanner().scan(_context(target, tmp_path / "out"), [target])

    assert len(metadata) == 1
    assert metadata[0].file == "x.gguf"
    assert metadata[0].kind == "gguf"
    assert metadata[0].metadata["magic"] == "GGUF"
    assert metadata[0].metadata["gguf_version"] == 3
    assert metadata[0].metadata["size_bytes"] == target.stat().st_size
    assert any(finding.category == "gguf_unusually_small" for finding in findings)


def test_gguf_invalid_magic_creates_high_severity_finding(tmp_path: Path) -> None:
    target = tmp_path / "bad.gguf"
    target.write_bytes(b"NOPE" + b"\x03\x00\x00\x00")

    metadata, findings = ModelMetadataScanner().scan(_context(target, tmp_path / "out"), [target])

    assert metadata[0].warnings == ["Invalid GGUF magic bytes."]
    assert any(
        finding.category == "gguf_invalid_magic" and finding.severity == Severity.HIGH and finding.scanner == "model_metadata"
        for finding in findings
    )


def test_safetensors_metadata_extracts_header_tensor_count_and_sample_names(tmp_path: Path) -> None:
    target = tmp_path / "model.safetensors"
    header = {
        "weight": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]},
        "__metadata__": {"format": "pt"},
    }
    target.write_bytes(_safetensors_bytes(header) + b"\x00\x00\x00\x00")

    metadata, findings = ModelMetadataScanner().scan(_context(target, tmp_path / "out"), [target])

    assert findings == []
    assert metadata[0].kind == "safetensors"
    assert metadata[0].metadata["tensor_count"] == 1
    assert metadata[0].metadata["metadata"] == {"format": "pt"}
    assert metadata[0].metadata["sample_tensor_names"] == ["weight"]


def test_safetensors_no_tensors_creates_medium_finding(tmp_path: Path) -> None:
    target = tmp_path / "empty.safetensors"
    target.write_bytes(_safetensors_bytes({"__metadata__": {"format": "pt"}}))

    metadata, findings = ModelMetadataScanner().scan(_context(target, tmp_path / "out"), [target])

    assert metadata[0].metadata["tensor_count"] == 0
    assert any(
        finding.category == "safetensors_no_tensors" and finding.severity == Severity.MEDIUM
        for finding in findings
    )


def test_safetensors_suspicious_metadata_creates_medium_finding(tmp_path: Path) -> None:
    target = tmp_path / "suspicious.safetensors"
    header = {
        "weight": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]},
        "__metadata__": {"download": "https://example.invalid/payload"},
    }
    target.write_bytes(_safetensors_bytes(header) + b"\x00\x00\x00\x00")

    _, findings = ModelMetadataScanner().scan(_context(target, tmp_path / "out"), [target])

    assert any(
        finding.category == "safetensors_suspicious_metadata"
        and finding.severity == Severity.MEDIUM
        and finding.scanner == "model_metadata"
        for finding in findings
    )


def test_safetensors_parse_error_creates_high_finding(tmp_path: Path) -> None:
    target = tmp_path / "broken.safetensors"
    target.write_bytes(b"not enough")

    metadata, findings = ModelMetadataScanner().scan(_context(target, tmp_path / "out"), [target])

    assert metadata[0].warnings
    assert any(
        finding.category == "safetensors_parse_error" and finding.severity == Severity.HIGH
        for finding in findings
    )


def test_unsupported_extension_is_ignored(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("hello\n", encoding="utf-8")

    metadata, findings = ModelMetadataScanner().scan(_context(target, tmp_path / "out"), [target])

    assert metadata == []
    assert findings == []
