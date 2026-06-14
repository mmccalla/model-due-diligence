"""Path and log sanitisation helpers for the mdd-ui API layer."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path, PurePosixPath

MAX_PATH_TARGET_LENGTH = 4096
_LOG_SAFE_PATTERN = re.compile(r"[\r\n\t]+")


def sanitize_log_field(value: str, *, max_length: int = 240) -> str:
    """Return a single-line log field safe from log-injection control characters."""

    collapsed = _LOG_SAFE_PATTERN.sub(" ", value.strip())
    return collapsed[:max_length]


def resolve_scan_target(raw_target: str) -> Path:
    """Resolve and validate a filesystem scan target from operator input.

    mdd-ui is a localhost-only operator tool. Path targets are intentionally
    user-controlled scan roots, matching the CLI contract.
    """

    cleaned = raw_target.strip()
    if not cleaned or len(cleaned) > MAX_PATH_TARGET_LENGTH:
        raise ValueError("Invalid scan target path.")
    if "\0" in cleaned:
        raise ValueError("Invalid scan target path.")

    posix = cleaned.replace("\\", "/")
    if ".." in PurePosixPath(posix).parts:
        raise ValueError("Path traversal is not allowed.")

    target = _resolve_from_allowed_anchor(posix)
    if not _is_allowed_scan_root(target):
        raise ValueError("Scan target must be under the user home, temp, or current working directory.")
    if not target.exists():
        raise FileNotFoundError(f"Target does not exist: {target}")
    return target


def _resolve_from_allowed_anchor(posix: str) -> Path:
    """Build an absolute path from validated components under a fixed anchor."""

    if posix == "~" or posix.startswith("~/"):
        relative = posix[2:] if posix.startswith("~/") else ""
        return _join_under_root(Path.home(), relative)
    if posix.startswith("/"):
        return _join_under_root(Path("/"), posix.lstrip("/"))
    return _join_under_root(Path.cwd(), posix)


def _join_under_root(root: Path, relative: str) -> Path:
    parts = _validated_relative_parts(relative)
    if not parts:
        return root.resolve()
    return root.joinpath(*parts).resolve()


def _validated_relative_parts(relative: str) -> tuple[str, ...]:
    if not relative:
        return ()
    parts = PurePosixPath(relative.replace("\\", "/")).parts
    if ".." in parts:
        raise ValueError("Path traversal is not allowed.")
    return parts


def _allowed_roots() -> tuple[Path, ...]:
    return (
        Path.home().resolve(),
        Path.cwd().resolve(),
        Path(tempfile.gettempdir()).resolve(),
    )


def _is_allowed_scan_root(path: Path) -> bool:
    resolved = path.resolve()
    return any(resolved == root or root in resolved.parents for root in _allowed_roots())
