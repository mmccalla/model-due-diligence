"""Unit tests for Ollama manifest resolution and staging helpers."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from tests.helpers_ollama import build_fake_ollama_store

from model_due_diligence.ollama import (
    MODEL_MEDIA_TYPE,
    blob_path_for_digest,
    digest_suffix,
    guess_model_extension,
    manifest_relative_parts,
    resolve_installed_model,
    stage_model_for_scan,
)


def test_manifest_relative_parts_for_unqualified_model() -> None:
    assert manifest_relative_parts("llama3:8b") == ("registry.ollama.ai", "library", "llama3", "8b")


def test_manifest_relative_parts_for_hugging_face_style_model() -> None:
    assert manifest_relative_parts("hf.co/Qwen/Qwen3-8B-GGUF:Q4_K_M") == (
        "hf.co",
        "Qwen",
        "Qwen3-8B-GGUF",
        "Q4_K_M",
    )


def test_digest_suffix_strips_algorithm_prefix() -> None:
    assert digest_suffix("sha256:abcdef") == "abcdef"


def test_guess_model_extension_detects_gguf(tmp_path: Path) -> None:
    blob = tmp_path / "blob"
    blob.write_bytes(b"GGUF" + b"\x03\x00\x00\x00")

    assert guess_model_extension(blob) == ".gguf"


def test_guess_model_extension_detects_safetensors(tmp_path: Path) -> None:
    blob = tmp_path / "blob"
    header = json.dumps({"weight": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}}).encode("utf-8")
    blob.write_bytes(struct.pack("<Q", len(header)) + header + b"\x00\x00\x00\x00")

    assert guess_model_extension(blob) == ".safetensors"


def test_resolve_installed_model_reads_manifest_and_layers(tmp_path: Path) -> None:
    models_dir = build_fake_ollama_store(tmp_path, "qwen3:4b")

    resolved = resolve_installed_model("qwen3:4b", models_dir=models_dir)

    assert resolved.model_name == "qwen3:4b"
    assert resolved.manifest_path.name == "4b"
    assert resolved.layers[0].media_type == MODEL_MEDIA_TYPE
    assert resolved.layers[0].blob_path.exists()


def test_blob_path_for_digest_returns_expected_path(tmp_path: Path) -> None:
    models_dir = build_fake_ollama_store(tmp_path, "qwen3:4b")

    path = blob_path_for_digest(models_dir, "sha256:model")

    assert path == models_dir / "blobs" / "sha256-model"


def test_stage_model_for_scan_creates_friendly_scan_files(tmp_path: Path) -> None:
    models_dir = build_fake_ollama_store(tmp_path, "qwen3:4b")
    resolved = resolve_installed_model("qwen3:4b", models_dir=models_dir)

    stage_path, temp_dir = stage_model_for_scan(resolved)
    try:
        assert (stage_path / "model.gguf").exists()
        assert (stage_path / "manifest.json").exists()
        assert (stage_path / "config.json").exists()
        assert (stage_path / "template.txt").exists()
        assert (stage_path / "license.txt").exists()
        assert (stage_path / "params.json").exists()
        assert (stage_path / "ollama-model.json").exists()
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()
