"""Tests for pip-audit dependency file discovery."""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.domain.models import ScanContext
from model_due_diligence.external.pip_audit import PipAuditAdapter


def _context_for(tmp_path: Path, target: Path) -> ScanContext:
    return ScanContext(
        target=target,
        root=target if target.is_dir() else target.parent,
        output_dir=tmp_path / "out",
        timeout_seconds=30,
    )


def test_find_dependency_files_includes_all_supported_names(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    (repo / "requirements-dev.txt").write_text("pytest\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

    files = PipAuditAdapter._find_dependency_files(_context_for(tmp_path, repo))

    assert [path.name for path in files] == ["pyproject.toml", "requirements-dev.txt", "requirements.txt"]


def test_find_dependency_files_returns_single_file_target(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("requests==2.31.0\n", encoding="utf-8")

    files = PipAuditAdapter._find_dependency_files(_context_for(tmp_path, requirements))

    assert files == [requirements]
