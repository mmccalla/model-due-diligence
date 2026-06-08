"""Shared external command runner.

This module centralises subprocess execution for external scanner adapters. It
is intentionally small, defensive and side-effect limited: callers provide the
command, working directory, timeout and expected output files; this module
returns a normalised `CommandResult` without raising for non-zero exit codes.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from collections.abc import Sequence
from os import environ
from pathlib import Path

from model_due_diligence.config.defaults import DEFAULT_TIMEOUT_SECONDS
from model_due_diligence.domain.models import CommandResult

MAX_CAPTURED_OUTPUT_CHARS = 20_000
TIMEOUT_EXIT_CODE = 124
_REMOVED_ENVIRONMENT_KEYS = {
    "COVERAGE_FILE",
    "COVERAGE_PROCESS_START",
    "PYTEST_CURRENT_TEST",
    "PYTEST_VERSION",
    "COV_CORE_CONFIG",
    "COV_CORE_DATAFILE",
    "COV_CORE_SOURCE",
}


def truncate(value: str, max_length: int = MAX_CAPTURED_OUTPUT_CHARS) -> str:
    """Return a bounded string suitable for reports and JSON output."""

    if len(value) <= max_length:
        return value

    return value[:max_length] + "\n...[truncated]..."


def run_command(
    tool: str,
    command: Sequence[str],
    cwd: Path | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    output_files: Sequence[Path] = (),
) -> CommandResult:
    """Run an external command and return a normalised command result.

    The command is not executed through a shell. Non-zero exit codes are
    captured in the result rather than raised. Missing executables are reported
    as `available=False` so scanner adapters can produce consistent findings.
    """

    if not command:
        return CommandResult(
            tool=tool,
            available=False,
            command=[],
            exit_code=None,
            stderr="No command was provided.",
            output_files=_stringify_paths(output_files),
            duration_seconds=0.0,
        )

    executable = command[0]
    if shutil.which(executable) is None:
        return CommandResult(
            tool=tool,
            available=False,
            command=list(command),
            output_files=_stringify_paths(output_files),
            duration_seconds=0.0,
        )

    started = time.monotonic()
    child_env = _sanitised_child_environment()

    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=child_env,
        )
        return CommandResult(
            tool=tool,
            available=True,
            command=list(command),
            exit_code=completed.returncode,
            stdout=truncate(completed.stdout),
            stderr=truncate(completed.stderr),
            output_files=_stringify_paths(output_files),
            duration_seconds=_elapsed_seconds(started),
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _normalise_timeout_output(exc.stdout)
        stderr = _normalise_timeout_output(exc.stderr) or "Command timed out."
        return CommandResult(
            tool=tool,
            available=True,
            command=list(command),
            exit_code=TIMEOUT_EXIT_CODE,
            stdout=truncate(stdout),
            stderr=truncate(stderr),
            output_files=_stringify_paths(output_files),
            duration_seconds=_elapsed_seconds(started),
        )
    except OSError as exc:
        return CommandResult(
            tool=tool,
            available=True,
            command=list(command),
            exit_code=None,
            stdout="",
            stderr=truncate(str(exc)),
            output_files=_stringify_paths(output_files),
            duration_seconds=_elapsed_seconds(started),
        )


def _normalise_timeout_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _stringify_paths(paths: Sequence[Path]) -> list[str]:
    return [str(path) for path in paths]


def _elapsed_seconds(started: float) -> float:
    return round(time.monotonic() - started, 3)


def _sanitised_child_environment() -> dict[str, str]:
    return {key: value for key, value in environ.items() if key not in _REMOVED_ENVIRONMENT_KEYS}
