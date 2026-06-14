"""Managed scan output directories for the mdd-ui API."""

from __future__ import annotations

import re
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from model_due_diligence.config.defaults import (
    REPORT_JSON_FILENAME,
    REPORT_MARKDOWN_FILENAME,
    REPORT_SARIF_FILENAME,
    SUPPORTED_REPORT_FORMATS,
)

SCAN_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
DEFAULT_OUTPUT_ROOT = Path.home() / ".cache" / "model-due-diligence" / "ui-scans"
DEFAULT_MAX_AGE_SECONDS = 86_400
DEFAULT_MAX_DIRS = 50

EXPORT_FILENAMES = {
    "markdown": REPORT_MARKDOWN_FILENAME,
    "json": REPORT_JSON_FILENAME,
    "sarif": REPORT_SARIF_FILENAME,
}


@dataclass(frozen=True, slots=True)
class ScanOutputManager:
    """Create, resolve and retire on-disk scan report directories."""

    root: Path
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS
    max_dirs: int = DEFAULT_MAX_DIRS

    def create_output_dir(self) -> tuple[str, Path]:
        """Allocate a new scan directory and remove stale artefacts first."""

        self.cleanup_stale()
        self.root.mkdir(parents=True, exist_ok=True)
        scan_id = uuid.uuid4().hex
        output_dir = (self.root / scan_id).resolve()
        output_dir.mkdir(parents=True, exist_ok=False)
        return scan_id, output_dir

    def resolve_scan_dir(self, scan_id: str) -> Path:
        """Return the scan directory for a valid identifier."""

        if not SCAN_ID_PATTERN.fullmatch(scan_id):
            raise ValueError(f"Invalid scan id: {scan_id!r}")

        scan_dir = (self.root / scan_id).resolve()
        root = self.root.resolve()
        if scan_dir != root and root not in scan_dir.parents:
            raise ValueError(f"Invalid scan id: {scan_id!r}")
        if not scan_dir.is_dir():
            raise FileNotFoundError(f"Scan output not found: {scan_id}")
        return scan_dir

    def resolve_export_path(self, scan_id: str, report_format: str) -> Path:
        """Return an export file path constrained to a known scan directory."""

        if report_format not in SUPPORTED_REPORT_FORMATS:
            raise ValueError(f"Unsupported export format: {report_format!r}")

        scan_dir = self.resolve_scan_dir(scan_id)
        export_path = (scan_dir / EXPORT_FILENAMES[report_format]).resolve()
        if export_path != scan_dir and scan_dir not in export_path.parents:
            raise ValueError(f"Invalid export path for scan: {scan_id}")
        if not export_path.is_file():
            raise FileNotFoundError(f"Export not found for scan {scan_id}: {report_format}")
        return export_path

    def cleanup_stale(self) -> None:
        """Remove expired scan directories to cap disk usage."""

        if not self.root.is_dir():
            return

        now = time.time()
        candidates: list[tuple[float, Path]] = []
        for child in self.root.iterdir():
            if not child.is_dir() or not SCAN_ID_PATTERN.fullmatch(child.name):
                continue
            try:
                mtime = child.stat().st_mtime
            except OSError:
                continue
            candidates.append((mtime, child))

        candidates.sort(key=lambda item: item[0])
        for mtime, child in candidates:
            if now - mtime > self.max_age_seconds:
                shutil.rmtree(child, ignore_errors=True)

        remaining = [child for child in self.root.iterdir() if child.is_dir() and SCAN_ID_PATTERN.fullmatch(child.name)]
        overflow = len(remaining) - self.max_dirs
        if overflow <= 0:
            return

        remaining.sort(key=lambda path: path.stat().st_mtime)
        for child in remaining[:overflow]:
            shutil.rmtree(child, ignore_errors=True)


def default_output_manager() -> ScanOutputManager:
    """Build the default on-disk scan output manager."""

    return ScanOutputManager(root=DEFAULT_OUTPUT_ROOT)
