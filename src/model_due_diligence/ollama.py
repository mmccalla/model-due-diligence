"""Helpers for scanning locally installed Ollama model artefacts.

The core scanner works on filesystem paths only. This module resolves an
installed Ollama model reference to its manifest and blob files, then stages a
scan-friendly temporary directory with stable filenames before handing it to the
normal scanner flow.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_OLLAMA_MODELS_DIR = Path.home() / ".ollama" / "models"
DEFAULT_OLLAMA_REGISTRY = "registry.ollama.ai"
DEFAULT_OLLAMA_NAMESPACE = "library"
OLLAMA_MODELS_ENV = "OLLAMA_MODELS"
GGUF_MAGIC = b"GGUF"
MAX_SAFETENSORS_HEADER_BYTES = 1024 * 1024
SMALL_BLOB_COPY_BYTES = 16 * 1024 * 1024
SAFETENSORS_HEADER_PREFIX_BYTES = 8

MODEL_MEDIA_TYPE = "application/vnd.ollama.image.model"
CONFIG_MEDIA_TYPE = "application/vnd.docker.container.image.v1+json"

TEXT_LAYER_FILENAMES: dict[str, str] = {
    "application/vnd.ollama.image.license": "license.txt",
    "application/vnd.ollama.image.system": "system.txt",
    "application/vnd.ollama.image.template": "template.txt",
}

JSON_LAYER_FILENAMES: dict[str, str] = {
    "application/vnd.ollama.image.params": "params.json",
}


@dataclass(frozen=True, slots=True)
class OllamaLayer:
    media_type: str
    digest: str
    size: int
    blob_path: Path


@dataclass(frozen=True, slots=True)
class OllamaModel:
    model_name: str
    models_dir: Path
    manifest_path: Path
    manifest: dict[str, Any]
    config_blob_path: Path
    layers: tuple[OllamaLayer, ...]


def default_ollama_models_dir() -> Path:
    """Return the configured Ollama models directory."""

    return Path(os.environ.get(OLLAMA_MODELS_ENV, str(DEFAULT_OLLAMA_MODELS_DIR))).expanduser()


def resolve_installed_model(model_name: str, models_dir: Path | None = None) -> OllamaModel:
    """Resolve an installed Ollama model reference to local manifest/blob paths."""

    resolved_models_dir = (models_dir or default_ollama_models_dir()).expanduser().resolve()
    manifest_path = resolved_models_dir / "manifests" / Path(*manifest_relative_parts(model_name))
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Ollama manifest not found for {model_name!r}: {manifest_path}. "
            "Check the installed model name and OLLAMA_MODELS location."
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = _manifest_section_as_dict(manifest, "config")
    config_blob_path = blob_path_for_digest(resolved_models_dir, str(config.get("digest", "")))
    layers = tuple(_layers_from_manifest(resolved_models_dir, manifest))

    return OllamaModel(
        model_name=model_name,
        models_dir=resolved_models_dir,
        manifest_path=manifest_path,
        manifest=manifest,
        config_blob_path=config_blob_path,
        layers=layers,
    )


def manifest_relative_parts(model_name: str) -> tuple[str, ...]:
    """Return manifest path components for an Ollama model reference."""

    cleaned = model_name.strip()
    if not cleaned:
        raise ValueError("Ollama model name must not be empty.")

    repository, tag = _split_model_reference(cleaned)
    repository_parts = repository.split("/")

    if len(repository_parts) == 1:
        return (DEFAULT_OLLAMA_REGISTRY, DEFAULT_OLLAMA_NAMESPACE, repository_parts[0], tag)

    if _looks_like_registry(repository_parts[0]):
        return (*repository_parts, tag)

    return (DEFAULT_OLLAMA_REGISTRY, *repository_parts, tag)


def blob_path_for_digest(models_dir: Path, digest: str) -> Path:
    """Return the local Ollama blob path for a digest like ``sha256:abc...``."""

    if not digest or ":" not in digest:
        raise ValueError(f"Unsupported Ollama digest: {digest!r}")

    algorithm, value = digest.split(":", 1)
    blob_path = models_dir / "blobs" / f"{algorithm}-{value}"
    if not blob_path.is_file():
        raise FileNotFoundError(f"Referenced Ollama blob not found: {blob_path}")

    return blob_path


def stage_model_for_scan(
    model: OllamaModel,
    *,
    keep_directory: bool = False,
) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    """Create a temporary scan directory containing friendly links/copies."""

    if keep_directory:
        stage_path = Path(tempfile.mkdtemp(prefix="mdd-ollama-")).resolve()
        temp_dir: tempfile.TemporaryDirectory[str] | None = None
    else:
        temp_dir = tempfile.TemporaryDirectory(prefix="mdd-ollama-")
        stage_path = Path(temp_dir.name).resolve()

    _write_json(stage_path / "ollama-model.json", _stage_metadata(model))
    (stage_path / "manifest.json").write_text(
        json.dumps(model.manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    _stage_blob(model.config_blob_path, stage_path / "config.json")

    for index, layer in enumerate(model.layers, start=1):
        staged_name = staged_filename_for_layer(layer, index)
        _stage_blob(layer.blob_path, stage_path / staged_name)

    return stage_path, temp_dir


def staged_filename_for_layer(layer: OllamaLayer, index: int) -> str:
    """Return a scan-friendly filename for a staged Ollama layer."""

    if layer.media_type == MODEL_MEDIA_TYPE:
        return f"model{guess_model_extension(layer.blob_path)}"

    if layer.media_type in TEXT_LAYER_FILENAMES:
        return TEXT_LAYER_FILENAMES[layer.media_type]

    if layer.media_type in JSON_LAYER_FILENAMES:
        return JSON_LAYER_FILENAMES[layer.media_type]

    suffix = digest_suffix(layer.digest)
    return f"layer-{index}-{suffix}.blob"


def guess_model_extension(blob_path: Path) -> str:
    """Best-effort extension guess for an Ollama model blob."""

    try:
        with blob_path.open("rb") as file:
            header = file.read(16)
            if header.startswith(GGUF_MAGIC):
                return ".gguf"

            if _looks_like_safetensors(file, header):
                return ".safetensors"
    except OSError:
        return ".bin"

    return ".bin"


def digest_suffix(digest: str) -> str:
    """Return the value portion of an Ollama digest."""

    return digest.split(":", 1)[1] if ":" in digest else digest


def _split_model_reference(model_name: str) -> tuple[str, str]:
    if ":" not in model_name:
        return model_name, "latest"

    repository, tag = model_name.rsplit(":", 1)
    if not repository or not tag:
        raise ValueError(f"Unsupported Ollama model reference: {model_name!r}")

    return repository, tag


def _looks_like_registry(first_component: str) -> bool:
    return "." in first_component or ":" in first_component or first_component == "localhost"


def _manifest_section_as_dict(manifest: dict[str, Any], key: str) -> dict[str, Any]:
    value = manifest.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Ollama manifest field {key!r} is missing or not an object.")
    return value


def _layers_from_manifest(models_dir: Path, manifest: dict[str, Any]) -> list[OllamaLayer]:
    raw_layers = manifest.get("layers")
    if not isinstance(raw_layers, list):
        raise ValueError("Ollama manifest field 'layers' is missing or not a list.")

    layers: list[OllamaLayer] = []
    for layer in raw_layers:
        if not isinstance(layer, dict):
            raise ValueError("Ollama manifest contains a non-object layer entry.")

        digest = str(layer.get("digest", ""))
        media_type = str(layer.get("mediaType", ""))
        size = int(layer.get("size", 0))
        layers.append(
            OllamaLayer(
                media_type=media_type,
                digest=digest,
                size=size,
                blob_path=blob_path_for_digest(models_dir, digest),
            )
        )

    return layers


def _stage_blob(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        destination.hardlink_to(source)
        return
    except OSError:
        pass

    try:
        if source.stat().st_size <= SMALL_BLOB_COPY_BYTES:
            shutil.copy2(source, destination)
            return
    except OSError:
        pass

    destination.symlink_to(source)


def _stage_metadata(model: OllamaModel) -> dict[str, Any]:
    return {
        "model_name": model.model_name,
        "manifest_path": str(model.manifest_path),
        "models_dir": str(model.models_dir),
        "layers": [
            {
                "media_type": layer.media_type,
                "digest": layer.digest,
                "size": layer.size,
                "blob_path": str(layer.blob_path),
            }
            for layer in model.layers
        ],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _looks_like_safetensors(file: Any, header: bytes) -> bool:
    if len(header) < SAFETENSORS_HEADER_PREFIX_BYTES:
        return False

    header_length = int.from_bytes(header[:SAFETENSORS_HEADER_PREFIX_BYTES], "little", signed=False)
    if header_length <= 0 or header_length > MAX_SAFETENSORS_HEADER_BYTES:
        return False

    inline_header = header[SAFETENSORS_HEADER_PREFIX_BYTES:]
    remaining_length = max(0, header_length - len(inline_header))
    remainder = inline_header + file.read(remaining_length)
    if len(remainder) != header_length:
        return False

    try:
        parsed = json.loads(remainder.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False

    return isinstance(parsed, dict)
