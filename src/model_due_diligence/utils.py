"""Shared utility functions for model-due-diligence.

This module contains small, side-effect-limited helpers used across inventory,
scanners, reporting and CLI orchestration. Keep this module generic: it should
not contain scanner-specific rules or reporting policy.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from model_due_diligence.config.defaults import (
    DEFAULT_IGNORED_DIRECTORIES,
    KNOWN_TEXT_FILENAMES,
    MAX_TEXT_SCAN_BYTES,
    TEXT_EXTENSIONS,
)

DEFAULT_HASH_CHUNK_SIZE = 1024 * 1024


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return datetime.now(UTC).isoformat()


def sha256_file(path: Path, chunk_size: int = DEFAULT_HASH_CHUNK_SIZE) -> str:
    """Return the SHA-256 digest for a file without loading it all into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(path: Path, root: Path) -> str:
    """Return `path` relative to `root`, falling back to the absolute path."""

    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def is_probably_text(path: Path) -> bool:
    """Return true when a file name or extension suggests text content."""

    return path.suffix.lower() in TEXT_EXTENSIONS or path.name.lower() in KNOWN_TEXT_FILENAMES


def read_text_safely(path: Path, max_bytes: int = MAX_TEXT_SCAN_BYTES) -> str | None:
    """Read a bounded text file safely, returning None when it should be skipped."""

    try:
        if path.is_symlink() or path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def iter_files(target: Path) -> list[Path]:
    """Return sorted file and symlink paths under a target.

    Default ignored directories are skipped to avoid scanning virtual
environments, Git internals, caches and generated reports.
    """

    if target.is_file() or target.is_symlink():
        return [target]

    return sorted(
        path
        for path in target.rglob("*")
        if (path.is_file() or path.is_symlink()) and not _is_under_ignored_directory(path, target)
    )


def _is_under_ignored_directory(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        relative_parts = path.parts

    return any(part in DEFAULT_IGNORED_DIRECTORIES for part in relative_parts[:-1])
