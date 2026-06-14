"""Regression tests for repository git hooks."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMIT_MSG_HOOK = REPO_ROOT / ".githooks" / "commit-msg"
PRE_COMMIT_HOOK = REPO_ROOT / ".githooks" / "pre-commit"


def _run_commit_msg_hook(message: str, tmp_path: Path) -> str:
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text(message, encoding="utf-8")
    subprocess.run(
        [str(COMMIT_MSG_HOOK), str(msg_file)],
        check=True,
        cwd=REPO_ROOT,
    )
    return msg_file.read_text(encoding="utf-8")


def test_commit_msg_hook_strips_cursor_co_authored_by_trailer(tmp_path: Path) -> None:
    message = textwrap.dedent(
        """\
        test(ui): add hook regression coverage

        Co-authored-by: Cursor <cursoragent@cursor.com>
        """
    )

    cleaned = _run_commit_msg_hook(message, tmp_path)

    assert "Co-authored-by: Cursor" not in cleaned
    assert "test(ui): add hook regression coverage" in cleaned


def test_commit_msg_hook_strips_made_with_cursor_trailers(tmp_path: Path) -> None:
    message = textwrap.dedent(
        """\
        chore: strip attribution trailers

        Made-with: Cursor
        Made with Cursor
        """
    )

    cleaned = _run_commit_msg_hook(message, tmp_path)

    assert "Made-with: Cursor" not in cleaned
    assert "Made with Cursor" not in cleaned
    assert "chore: strip attribution trailers" in cleaned


def _init_temp_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], check=True, cwd=repo, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, cwd=repo)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, cwd=repo)
    return repo


def test_pre_commit_hook_rejects_staged_audit_report_json(tmp_path: Path) -> None:
    repo = _init_temp_git_repo(tmp_path)
    blocked_path = repo / "audit-smoke" / "model_due_diligence_report.json"
    blocked_path.parent.mkdir(parents=True)
    blocked_path.write_text('{"risk_level":"LOW"}', encoding="utf-8")

    subprocess.run(["git", "add", "audit-smoke/model_due_diligence_report.json"], check=True, cwd=repo)
    result = subprocess.run(
        [str(PRE_COMMIT_HOOK)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Refusing commit" in result.stderr
    assert "audit-smoke/model_due_diligence_report.json" in result.stderr


def test_pre_commit_hook_allows_non_audit_files(tmp_path: Path) -> None:
    repo = _init_temp_git_repo(tmp_path)
    readme = repo / "README.md"
    readme.write_text("# safe\n", encoding="utf-8")

    subprocess.run(["git", "add", "README.md"], check=True, cwd=repo)
    result = subprocess.run(
        [str(PRE_COMMIT_HOOK)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "staged_path",
    [
        "audit/output/model_due_diligence_report.json",
        "reports/modelscan.json",
        "scan/pip-audit-20260101.json",
    ],
)
def test_pre_commit_hook_rejects_other_blocked_scanner_outputs(
    tmp_path: Path,
    staged_path: str,
) -> None:
    repo = _init_temp_git_repo(tmp_path)
    blocked = repo / staged_path
    blocked.parent.mkdir(parents=True, exist_ok=True)
    blocked.write_text("{}", encoding="utf-8")

    subprocess.run(["git", "add", staged_path], check=True, cwd=repo)
    result = subprocess.run(
        [str(PRE_COMMIT_HOOK)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert staged_path in result.stderr
