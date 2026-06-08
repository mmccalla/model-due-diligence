from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from collections.abc import Sequence

from model_due_diligence.domain.models import CommandResult


def truncate(value: str, max_len: int = 20_000) -> str:
    return value if len(value) <= max_len else value[:max_len] + "\n...[truncated]..."


def run_command(tool: str, command: Sequence[str], cwd: Path | None = None, timeout_seconds: int = 300, output_files: Sequence[Path] = ()) -> CommandResult:
    if shutil.which(command[0]) is None:
        return CommandResult(tool=tool, available=False, command=list(command), output_files=[str(p) for p in output_files])
    try:
        completed = subprocess.run(list(command), cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout_seconds, check=False)
        return CommandResult(tool=tool, available=True, command=list(command), exit_code=completed.returncode, stdout=truncate(completed.stdout), stderr=truncate(completed.stderr), output_files=[str(p) for p in output_files])
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else "Command timed out"
        return CommandResult(tool=tool, available=True, command=list(command), exit_code=124, stdout=truncate(stdout), stderr=truncate(stderr), output_files=[str(p) for p in output_files])
