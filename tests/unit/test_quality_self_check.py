"""Tests for quality self-check project root resolution."""

from __future__ import annotations

from model_due_diligence.external.quality import scanner_project_root


def test_scanner_project_root_points_at_repository_root() -> None:
    root = scanner_project_root()

    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "model_due_diligence").is_dir()
