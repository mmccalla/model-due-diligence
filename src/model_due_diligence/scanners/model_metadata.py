from __future__ import annotations

import json
import re
import struct
from pathlib import Path
from collections.abc import Iterable
from typing import Any

from model_due_diligence.config.defaults import GGUF_MAGIC, SAFETENSORS_MAX_HEADER_BYTES
from model_due_diligence.domain.models import Finding, ModelMetadata, ScanContext, Severity
from model_due_diligence.utils import safe_relative


class ModelMetadataScanner:
    def scan(self, context: ScanContext, files: Iterable[Path]) -> tuple[list[ModelMetadata], list[Finding]]:
        metadata: list[ModelMetadata] = []
        findings: list[Finding] = []
        for path in files:
            if path.suffix.lower() == ".gguf":
                item, item_findings = self._scan_gguf(context, path)
                metadata.append(item); findings.extend(item_findings)
            elif path.suffix.lower() == ".safetensors":
                item, item_findings = self._scan_safetensors(context, path)
                metadata.append(item); findings.extend(item_findings)
        return metadata, findings

    def _scan_gguf(self, context: ScanContext, path: Path) -> tuple[ModelMetadata, list[Finding]]:
        relative = safe_relative(path, context.root); findings: list[Finding] = []; meta: dict[str, Any] = {}; warnings: list[str] = []
        try:
            with path.open("rb") as file:
                magic = file.read(4)
                if magic != GGUF_MAGIC:
                    findings.append(Finding(Severity.HIGH, "gguf_invalid_magic", relative, "File has .gguf extension but does not start with GGUF magic bytes.")); warnings.append("Invalid GGUF magic bytes.")
                else:
                    meta["magic"] = "GGUF"; data = file.read(4)
                    if len(data) == 4: meta["gguf_version"] = struct.unpack("<I", data)[0]
            if path.stat().st_size < 1024 * 1024:
                findings.append(Finding(Severity.MEDIUM, "gguf_unusually_small", relative, "GGUF file is unusually small for an LLM model.", evidence=f"size_bytes={path.stat().st_size}"))
        except OSError as exc:
            findings.append(Finding(Severity.MEDIUM, "gguf_read_error", relative, f"Could not inspect GGUF header: {exc}")); warnings.append(str(exc))
        return ModelMetadata(relative, "gguf", meta, warnings), findings

    def _scan_safetensors(self, context: ScanContext, path: Path) -> tuple[ModelMetadata, list[Finding]]:
        relative = safe_relative(path, context.root); findings: list[Finding] = []; meta: dict[str, Any] = {}; warnings: list[str] = []
        try:
            with path.open("rb") as file:
                raw = file.read(8)
                if len(raw) != 8: raise ValueError("Safetensors file is too short to contain a header length.")
                header_len = struct.unpack("<Q", raw)[0]; meta["header_length_bytes"] = header_len
                if header_len > SAFETENSORS_MAX_HEADER_BYTES:
                    findings.append(Finding(Severity.HIGH, "safetensors_header_too_large", relative, f"Safetensors header is unexpectedly large: {header_len} bytes."))
                    return ModelMetadata(relative, "safetensors", meta, warnings), findings
                parsed = json.loads(file.read(header_len).decode("utf-8"))
                tensor_names = [name for name in parsed if name != "__metadata__"]
                meta["tensor_count"] = len(tensor_names); meta["metadata"] = parsed.get("__metadata__", {}); meta["sample_tensor_names"] = tensor_names[:20]
                for key, value in self._find_suspicious_metadata(parsed.get("__metadata__", {})).items():
                    findings.append(Finding(Severity.MEDIUM, "safetensors_suspicious_metadata", relative, f"Suspicious safetensors metadata key/value: {key}", evidence=str(value)[:300]))
        except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError, struct.error) as exc:
            findings.append(Finding(Severity.HIGH, "safetensors_parse_error", relative, f"Could not parse safetensors header: {exc}")); warnings.append(str(exc))
        return ModelMetadata(relative, "safetensors", meta, warnings), findings

    @staticmethod
    def _find_suspicious_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        pattern = re.compile(r"(http://|https://|curl|wget|rm -rf|token|secret|password|BEGIN RSA|OPENAI_API_KEY|HF_TOKEN)", flags=re.IGNORECASE)
        return {key: value for key, value in metadata.items() if pattern.search(f"{key}={value}")}
