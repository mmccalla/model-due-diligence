from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from model_due_diligence.config.defaults import KNOWN_TEXT_FILENAMES, TEXT_EXTENSIONS


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def is_probably_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name.lower() in KNOWN_TEXT_FILENAMES


def read_text_safely(path: Path, max_bytes: int = 2_000_000) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def iter_files(target: Path) -> list[Path]:
    if target.is_file() or target.is_symlink():
        return [target]
    return sorted(p for p in target.rglob("*") if p.is_file() or p.is_symlink())
