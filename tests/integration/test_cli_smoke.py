"""CLI smoke tests for model-due-diligence.

These tests exercise the installed CLI path through `main()` without invoking
optional external scanners. They verify that the command can scan a harmless
local directory, write the expected reports and return the correct process exit
code for the configured risk threshold.
"""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.cli import main


def test_cli_smoke_skip_external_writes_default_reports(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    audit_dir = tmp_path / "audit"
    repo.mkdir()
    (repo / "README.md").write_text("hello\n", encoding="utf-8")

    exit_code = main(
        [
            str(repo),
            "--out",
            str(audit_dir),
            "--skip-external",
            "--fail-on",
            "critical",
        ]
    )

    assert exit_code == 0
    assert (audit_dir / "model_due_diligence_report.md").exists()
    assert (audit_dir / "model_due_diligence_report.json").exists()
    assert (audit_dir / "model_due_diligence_report.sarif").exists()


def test_cli_smoke_can_limit_report_formats(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    audit_dir = tmp_path / "audit-json-only"
    repo.mkdir()
    (repo / "README.md").write_text("hello\n", encoding="utf-8")

    exit_code = main(
        [
            str(repo),
            "--out",
            str(audit_dir),
            "--format",
            "json",
            "--skip-external",
            "--fail-on",
            "critical",
        ]
    )

    assert exit_code == 0
    assert (audit_dir / "model_due_diligence_report.json").exists()
    assert not (audit_dir / "model_due_diligence_report.md").exists()
    assert not (audit_dir / "model_due_diligence_report.sarif").exists()


def test_cli_returns_usage_error_for_missing_target(tmp_path: Path) -> None:
    missing_target = tmp_path / "missing"

    exit_code = main([str(missing_target), "--out", str(tmp_path / "audit")])

    assert exit_code == 2
