"""Unit tests for the shared external command runner."""

from __future__ import annotations

import sys
from pathlib import Path

from model_due_diligence.external import command_runner
from model_due_diligence.external.command_runner import TIMEOUT_EXIT_CODE, run_command, truncate


def test_missing_command_returns_unavailable_result() -> None:
    result = run_command("missing", ["definitely-not-a-real-command-xyz"])

    assert result.available is False
    assert result.tool == "missing"
    assert result.command == ["definitely-not-a-real-command-xyz"]
    assert result.exit_code is None
    assert result.duration_seconds == 0.0


def test_empty_command_returns_unavailable_result() -> None:
    result = run_command("empty", [])

    assert result.available is False
    assert result.tool == "empty"
    assert result.command == []
    assert result.exit_code is None
    assert result.stderr == "No command was provided."


def test_successful_command_captures_stdout(tmp_path: Path) -> None:
    result = run_command(
        "python",
        [sys.executable, "-c", "print('hello from command runner')"],
        cwd=tmp_path,
        timeout_seconds=10,
    )

    assert result.available is True
    assert result.exit_code == 0
    assert "hello from command runner" in result.stdout
    assert result.stderr == ""
    assert result.duration_seconds is not None
    assert result.duration_seconds >= 0.0


def test_non_zero_command_captures_exit_code_and_stderr(tmp_path: Path) -> None:
    result = run_command(
        "python",
        [sys.executable, "-c", "import sys; print('bad', file=sys.stderr); raise SystemExit(7)"],
        cwd=tmp_path,
        timeout_seconds=10,
    )

    assert result.available is True
    assert result.exit_code == 7
    assert "bad" in result.stderr


def test_timeout_returns_timeout_exit_code(tmp_path: Path) -> None:
    result = run_command(
        "python",
        [sys.executable, "-c", "import time; time.sleep(2)"],
        cwd=tmp_path,
        timeout_seconds=1,
    )

    assert result.available is True
    assert result.exit_code == TIMEOUT_EXIT_CODE
    assert "timed out" in result.stderr.lower()


def test_output_files_are_recorded(tmp_path: Path) -> None:
    output_path = tmp_path / "scanner-output.json"

    result = run_command(
        "python",
        [sys.executable, "-c", "print('{}')"],
        cwd=tmp_path,
        timeout_seconds=10,
        output_files=[output_path],
    )

    assert result.output_files == [str(output_path)]


def test_run_command_resolves_tool_from_active_interpreter_directory(monkeypatch, tmp_path: Path) -> None:
    venv_bin = tmp_path / "venv-bin"
    venv_bin.mkdir()
    tool_path = venv_bin / "fake-tool"
    tool_path.write_text("#!/bin/sh\necho resolved-from-interpreter-dir\n", encoding="utf-8")
    tool_path.chmod(0o755)

    real_python_dir = tmp_path / "real-python"
    real_python_dir.mkdir()
    python_link = venv_bin / "python"
    python_link.symlink_to(real_python_dir / "python3")

    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setattr(command_runner.sys, "executable", str(python_link))

    result = run_command("fake-tool", ["fake-tool"], cwd=tmp_path, timeout_seconds=10)

    assert result.available is True
    assert result.exit_code == 0
    assert "resolved-from-interpreter-dir" in result.stdout


def test_truncate_leaves_short_values_unchanged() -> None:
    assert truncate("short", max_length=10) == "short"


def test_truncate_marks_long_values() -> None:
    value = truncate("x" * 20, max_length=5)

    assert value.startswith("xxxxx")
    assert "[truncated]" in value
