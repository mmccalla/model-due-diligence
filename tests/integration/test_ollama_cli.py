"""Integration tests for the Ollama helper CLI."""

from __future__ import annotations

from pathlib import Path

from tests.helpers_ollama import build_fake_ollama_store

from model_due_diligence.ollama_cli import main


def test_ollama_cli_scans_fake_installed_model(tmp_path: Path) -> None:
    models_dir = build_fake_ollama_store(tmp_path, "qwen3:4b")
    output_dir = tmp_path / "audit"

    exit_code = main(
        [
            "qwen3:4b",
            "--ollama-models-dir",
            str(models_dir),
            "--out",
            str(output_dir),
            "--skip-external",
            "--fail-on",
            "critical",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "model_due_diligence_report.md").exists()
    assert (output_dir / "model_due_diligence_report.json").exists()
    assert (output_dir / "model_due_diligence_report.sarif").exists()
    assert "ollama:qwen3:4b" in (output_dir / "model_due_diligence_report.md").read_text(encoding="utf-8")
