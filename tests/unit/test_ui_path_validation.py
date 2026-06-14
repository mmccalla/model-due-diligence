"""Unit tests for mdd-ui path validation helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from model_due_diligence.ui.path_validation import resolve_scan_target, sanitize_log_field


def test_sanitize_log_field_strips_control_characters() -> None:
    assert sanitize_log_field("hello\nworld\r") == "hello world"


def test_resolve_scan_target_returns_existing_path(tmp_path: Path) -> None:
    target = tmp_path / "demo.gguf"
    target.write_bytes(b"GGUF")

    resolved = resolve_scan_target(str(target))

    assert resolved == target.resolve()


def test_resolve_scan_target_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Path traversal"):
        resolve_scan_target(str(tmp_path / ".." / "etc" / "passwd"))


def test_resolve_scan_target_raises_for_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="does not exist"):
        resolve_scan_target(str(tmp_path / "missing"))
