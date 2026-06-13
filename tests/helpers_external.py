"""Shared helpers for external scanner adapter tests."""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.domain.models import CommandResult, ScanContext


def scan_context(tmp_path: Path, *, target: Path | None = None) -> ScanContext:
    repo = target or (tmp_path / "repo")
    repo.mkdir(exist_ok=True)
    return ScanContext(
        target=repo,
        root=repo,
        output_dir=tmp_path / "out",
        timeout_seconds=30,
    )


def command_result(
    tool: str,
    *,
    available: bool = True,
    exit_code: int | None = 0,
    stdout: str = "",
    stderr: str = "",
    command: list[str] | None = None,
) -> CommandResult:
    return CommandResult(
        tool=tool,
        available=available,
        command=command or [tool],
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
    )
