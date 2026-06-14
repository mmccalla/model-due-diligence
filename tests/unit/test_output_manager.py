"""Unit tests for scan output lifecycle management."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from model_due_diligence.ui.output_manager import ScanOutputManager


def test_create_output_dir_allocates_scan_id(tmp_path: Path) -> None:
    manager = ScanOutputManager(root=tmp_path / "scans")

    scan_id, output_dir = manager.create_output_dir()

    assert len(scan_id) == 32
    assert output_dir.is_dir()
    assert output_dir.name == scan_id


def test_resolve_export_path_returns_existing_report(tmp_path: Path) -> None:
    manager = ScanOutputManager(root=tmp_path / "scans")
    scan_id, output_dir = manager.create_output_dir()
    report_path = output_dir / "model_due_diligence_report.md"
    report_path.write_text("# report\n", encoding="utf-8")

    export_path = manager.resolve_export_path(scan_id, "markdown")

    assert export_path == report_path


def test_cleanup_stale_removes_old_directories(tmp_path: Path) -> None:
    manager = ScanOutputManager(root=tmp_path / "scans", max_age_seconds=0, max_dirs=10)
    _, output_dir = manager.create_output_dir()
    assert output_dir.exists()

    old = time.time() - 10
    os.utime(output_dir, (old, old))
    manager.cleanup_stale()

    assert not output_dir.exists()


def test_resolve_export_path_rejects_invalid_scan_id(tmp_path: Path) -> None:
    manager = ScanOutputManager(root=tmp_path / "scans")

    with pytest.raises(ValueError, match="Invalid scan id"):
        manager.resolve_export_path("../escape", "json")
