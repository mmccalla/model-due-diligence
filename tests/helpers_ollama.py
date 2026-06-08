"""Shared Ollama test helpers."""

from __future__ import annotations

import json
from pathlib import Path

from model_due_diligence.ollama import MODEL_MEDIA_TYPE, manifest_relative_parts


def build_fake_ollama_store(root: Path, model_name: str) -> Path:
    models_dir = root / "models"
    manifest_path = models_dir / "manifests" / Path(*manifest_relative_parts(model_name))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    blobs_dir = models_dir / "blobs"
    blobs_dir.mkdir(parents=True, exist_ok=True)

    _write_blob(blobs_dir / "sha256-config", b'{"architecture":"llama"}\n')
    _write_blob(blobs_dir / "sha256-model", b"GGUF" + b"\x03\x00\x00\x00" + b"0" * 32)
    _write_blob(blobs_dir / "sha256-template", b"{{ .Prompt }}\n")
    _write_blob(blobs_dir / "sha256-license", b"apache-2.0\n")
    _write_blob(blobs_dir / "sha256-params", b'{"temperature":0.1}\n')

    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "digest": "sha256:config",
            "size": 24,
        },
        "layers": [
            {
                "mediaType": MODEL_MEDIA_TYPE,
                "digest": "sha256:model",
                "size": 40,
            },
            {
                "mediaType": "application/vnd.ollama.image.template",
                "digest": "sha256:template",
                "size": 13,
            },
            {
                "mediaType": "application/vnd.ollama.image.license",
                "digest": "sha256:license",
                "size": 11,
            },
            {
                "mediaType": "application/vnd.ollama.image.params",
                "digest": "sha256:params",
                "size": 20,
            },
        ],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    return models_dir


def _write_blob(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
