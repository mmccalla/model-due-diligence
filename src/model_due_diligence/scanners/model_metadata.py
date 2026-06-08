"""Model metadata scanner.

This scanner performs static header-level inspection of model artefacts whose
formats are expected to be safer than pickle-style serialisation. It currently
supports GGUF and safetensors.

The scanner does not load model weights. Metadata findings are review signals,
not proof that a model is safe or compromised.
"""

from __future__ import annotations

import json
import re
import struct
from collections.abc import Iterable
from pathlib import Path
from typing import Any, BinaryIO, cast

from model_due_diligence.config.defaults import GGUF_MAGIC, SAFETENSORS_MAX_HEADER_BYTES
from model_due_diligence.domain.models import Finding, ModelMetadata, ScanContext, Severity
from model_due_diligence.utils import safe_relative


class ModelMetadataScanner:
    """Extract static metadata from supported model file formats."""

    scanner_name = "model_metadata"
    gguf_min_expected_size_bytes = 1024 * 1024
    metadata_evidence_max_chars = 300
    gguf_version_bytes = 4
    safetensors_header_prefix_bytes = 8

    def scan(self, context: ScanContext, files: Iterable[Path]) -> tuple[list[ModelMetadata], list[Finding]]:
        """Scan supported model files and return metadata plus findings."""

        metadata: list[ModelMetadata] = []
        findings: list[Finding] = []

        for path in files:
            suffix = path.suffix.lower()

            if suffix == ".gguf":
                item, item_findings = self._scan_gguf(context, path)
            elif suffix == ".safetensors":
                item, item_findings = self._scan_safetensors(context, path)
            else:
                continue

            metadata.append(item)
            findings.extend(item_findings)

        return metadata, findings

    def _scan_gguf(self, context: ScanContext, path: Path) -> tuple[ModelMetadata, list[Finding]]:
        relative = safe_relative(path, context.root)
        findings: list[Finding] = []
        meta: dict[str, Any] = {}
        warnings: list[str] = []

        try:
            with path.open("rb") as file:
                magic = file.read(4)
                if magic != GGUF_MAGIC:
                    warnings.append("Invalid GGUF magic bytes.")
                    findings.append(self._gguf_invalid_magic_finding(relative))
                else:
                    meta["magic"] = "GGUF"
                    version = self._read_gguf_version(file)
                    if version is not None:
                        meta["gguf_version"] = version

            size_bytes = path.stat().st_size
            meta["size_bytes"] = size_bytes
            if size_bytes < self.gguf_min_expected_size_bytes:
                findings.append(self._gguf_unusually_small_finding(relative, size_bytes))

        except OSError as exc:
            warnings.append(str(exc))
            findings.append(self._gguf_read_error_finding(relative, exc))

        return ModelMetadata(file=relative, kind="gguf", metadata=meta, warnings=warnings), findings

    @staticmethod
    def _read_gguf_version(file: BinaryIO) -> int | None:
        data = file.read(ModelMetadataScanner.gguf_version_bytes)
        if len(data) != ModelMetadataScanner.gguf_version_bytes:
            return None
        return cast(int, struct.unpack("<I", data)[0])

    def _scan_safetensors(self, context: ScanContext, path: Path) -> tuple[ModelMetadata, list[Finding]]:
        relative = safe_relative(path, context.root)
        findings: list[Finding] = []
        meta: dict[str, Any] = {}
        warnings: list[str] = []

        try:
            parsed = self._read_safetensors_header(path, meta)
            tensor_names = [name for name in parsed if name != "__metadata__"]
            metadata = parsed.get("__metadata__", {})

            meta["tensor_count"] = len(tensor_names)
            meta["metadata"] = metadata
            meta["sample_tensor_names"] = tensor_names[:20]

            if not tensor_names:
                findings.append(self._safetensors_no_tensors_finding(relative))

            for key, value in self._find_suspicious_metadata(metadata).items():
                findings.append(self._safetensors_suspicious_metadata_finding(relative, key, value))

        except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError, struct.error) as exc:
            warnings.append(str(exc))
            findings.append(self._safetensors_parse_error_finding(relative, exc))

        return ModelMetadata(file=relative, kind="safetensors", metadata=meta, warnings=warnings), findings

    def _read_safetensors_header(self, path: Path, meta: dict[str, Any]) -> dict[str, Any]:
        with path.open("rb") as file:
            raw_header_length = file.read(self.safetensors_header_prefix_bytes)
            if len(raw_header_length) != self.safetensors_header_prefix_bytes:
                raise ValueError("Safetensors file is too short to contain a header length.")

            header_length = struct.unpack("<Q", raw_header_length)[0]
            meta["header_length_bytes"] = header_length

            if header_length > SAFETENSORS_MAX_HEADER_BYTES:
                raise ValueError(f"Safetensors header is unexpectedly large: {header_length} bytes.")

            header_bytes = file.read(header_length)
            if len(header_bytes) != header_length:
                raise ValueError("Safetensors file ended before the full header could be read.")

            parsed = json.loads(header_bytes.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise ValueError("Safetensors header JSON is not an object.")

            return parsed

    def _gguf_invalid_magic_finding(self, relative: str) -> Finding:
        return Finding(
            severity=Severity.HIGH,
            category="gguf_invalid_magic",
            file=relative,
            message="File has .gguf extension but does not start with GGUF magic bytes.",
            recommendation="Do not load. Verify file provenance and redownload from the source repository.",
            scanner=self.scanner_name,
        )

    def _gguf_unusually_small_finding(self, relative: str, size_bytes: int) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="gguf_unusually_small",
            file=relative,
            message="GGUF file is unusually small for an LLM model.",
            evidence=f"size_bytes={size_bytes}; threshold={self.gguf_min_expected_size_bytes}",
            recommendation="Verify this is not a placeholder, pointer file or tampered artefact.",
            scanner=self.scanner_name,
        )

    def _gguf_read_error_finding(self, relative: str, exc: OSError) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="gguf_read_error",
            file=relative,
            message=f"Could not inspect GGUF header: {exc}",
            recommendation="Review filesystem permissions and rerun the scan.",
            scanner=self.scanner_name,
        )

    def _safetensors_no_tensors_finding(self, relative: str) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="safetensors_no_tensors",
            file=relative,
            message="Safetensors file contains no tensor entries.",
            recommendation="Verify this file is expected and has not been corrupted or replaced.",
            scanner=self.scanner_name,
        )

    def _safetensors_suspicious_metadata_finding(self, relative: str, key: str, value: Any) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="safetensors_suspicious_metadata",
            file=relative,
            message=f"Suspicious safetensors metadata key/value: {key}",
            evidence=str(value)[: self.metadata_evidence_max_chars],
            recommendation=(
                "Review metadata. Metadata is not normally executable, but suspicious values can indicate "
                "weak provenance, tampering or prompt-level risk."
            ),
            scanner=self.scanner_name,
        )

    def _safetensors_parse_error_finding(self, relative: str, exc: Exception) -> Finding:
        return Finding(
            severity=Severity.HIGH,
            category="safetensors_parse_error",
            file=relative,
            message=f"Could not parse safetensors header: {exc}",
            recommendation="Do not load this artefact until the parse error is reviewed and explained.",
            scanner=self.scanner_name,
        )

    @staticmethod
    def _find_suspicious_metadata(metadata: object) -> dict[str, Any]:
        if not isinstance(metadata, dict):
            return {}

        pattern = re.compile(
            r"(http://|https://|curl|wget|rm -rf|token|secret|password|BEGIN RSA|BEGIN OPENSSH|"
            r"BEGIN PRIVATE KEY|OPENAI_API_KEY|HF_TOKEN|HUGGINGFACE_TOKEN|GITHUB_TOKEN)",
            flags=re.IGNORECASE,
        )

        return {str(key): value for key, value in metadata.items() if pattern.search(f"{key}={value}")}
