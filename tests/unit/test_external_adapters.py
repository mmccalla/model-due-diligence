"""Unit tests for external scanner adapters with mocked subprocess execution."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from tests.helpers_external import command_result, scan_context

from model_due_diligence.domain.models import Severity
from model_due_diligence.external.bandit import BanditAdapter
from model_due_diligence.external.detect_secrets import DetectSecretsAdapter
from model_due_diligence.external.modelscan import ModelScanAdapter
from model_due_diligence.external.quality import QualitySelfCheckAdapter, scanner_project_root
from model_due_diligence.external.scanner_runner import ExternalScannerRunner
from model_due_diligence.external.semgrep import SemgrepAdapter


@pytest.mark.parametrize(
    ("adapter_cls", "tool_name", "findings_exit_code", "expected_severity"),
    [
        (BanditAdapter, "bandit", 1, Severity.MEDIUM),
        (SemgrepAdapter, "semgrep", 1, Severity.MEDIUM),
        (ModelScanAdapter, "modelscan", 1, Severity.HIGH),
    ],
)
def test_external_adapters_normalise_unavailable_tool(
    adapter_cls: type[BanditAdapter],
    tool_name: str,
    findings_exit_code: int,
    expected_severity: Severity,
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    adapter = adapter_cls()
    context = scan_context(tmp_path)

    monkeypatch.setattr(
        f"model_due_diligence.external.{tool_name}.run_command",
        lambda **_: command_result(tool_name, available=False),
    )

    result = adapter.run(context)

    assert len(result.findings) == 1
    assert result.findings[0].category == "scanner_unavailable"
    assert result.findings[0].severity == Severity.LOW


@pytest.mark.parametrize(
    ("adapter_cls", "tool_name"),
    [
        (BanditAdapter, "bandit"),
        (SemgrepAdapter, "semgrep"),
        (ModelScanAdapter, "modelscan"),
    ],
)
def test_external_adapters_return_no_findings_on_success(
    adapter_cls: type[BanditAdapter],
    tool_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    adapter = adapter_cls()
    context = scan_context(tmp_path)

    monkeypatch.setattr(
        f"model_due_diligence.external.{tool_name}.run_command",
        lambda **_: command_result(tool_name, exit_code=0),
    )

    result = adapter.run(context)

    assert result.findings == []


@pytest.mark.parametrize(
    ("adapter_cls", "tool_name", "expected_severity"),
    [
        (BanditAdapter, "bandit", Severity.MEDIUM),
        (SemgrepAdapter, "semgrep", Severity.MEDIUM),
        (ModelScanAdapter, "modelscan", Severity.HIGH),
    ],
)
def test_external_adapters_normalise_scanner_findings_exit_code(
    adapter_cls: type[BanditAdapter],
    tool_name: str,
    expected_severity: Severity,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    adapter = adapter_cls()
    context = scan_context(tmp_path)

    monkeypatch.setattr(
        f"model_due_diligence.external.{tool_name}.run_command",
        lambda **_: command_result(tool_name, exit_code=1, stderr="findings present"),
    )

    result = adapter.run(context)

    assert len(result.findings) == 1
    assert result.findings[0].category == "external_scanner_findings"
    assert result.findings[0].severity == expected_severity


@pytest.mark.parametrize(
    ("adapter_cls", "tool_name"),
    [
        (BanditAdapter, "bandit"),
        (SemgrepAdapter, "semgrep"),
        (ModelScanAdapter, "modelscan"),
    ],
)
def test_external_adapters_normalise_unexpected_exit_code(
    adapter_cls: type[BanditAdapter],
    tool_name: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    adapter = adapter_cls()
    context = scan_context(tmp_path)

    monkeypatch.setattr(
        f"model_due_diligence.external.{tool_name}.run_command",
        lambda **_: command_result(tool_name, exit_code=2, stderr="unexpected failure"),
    )

    result = adapter.run(context)

    assert len(result.findings) == 1
    assert result.findings[0].category == "external_scanner_error"
    assert result.findings[0].severity == Severity.MEDIUM


def test_detect_secrets_reports_findings_from_stdout_baseline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    adapter = DetectSecretsAdapter()
    context = scan_context(tmp_path)
    stdout = '{"results": {"file.py": [{"type": "Secret"}]}}'

    monkeypatch.setattr(
        "model_due_diligence.external.detect_secrets.run_command",
        lambda **_: command_result("detect-secrets", exit_code=0, stdout=stdout),
    )

    result = adapter.run(context)

    assert len(result.findings) == 1
    assert result.findings[0].category == "external_scanner_findings"


def test_detect_secrets_returns_clean_result_for_empty_baseline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    adapter = DetectSecretsAdapter()
    context = scan_context(tmp_path)

    monkeypatch.setattr(
        "model_due_diligence.external.detect_secrets.run_command",
        lambda **_: command_result("detect-secrets", exit_code=0, stdout='{"results": {}}'),
    )

    result = adapter.run(context)

    assert result.findings == []


def test_quality_self_check_runs_against_scanner_project_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    adapter = QualitySelfCheckAdapter()
    context = scan_context(tmp_path)
    observed_cwds: list[Path] = []

    def fake_run_command(*, cwd: Path, **_: Any) -> Any:
        observed_cwds.append(cwd)
        return command_result("self_ruff_format_check", exit_code=0)

    monkeypatch.setattr("model_due_diligence.external.quality.run_command", fake_run_command)

    results = adapter.run(context)

    assert len(results) == 4
    assert observed_cwds
    assert all(cwd == scanner_project_root() for cwd in observed_cwds)


def test_scanner_runner_skips_external_tools_when_requested(tmp_path: Path) -> None:
    context = replace(scan_context(tmp_path), skip_external=True)

    tools, findings = ExternalScannerRunner().run_all(context)

    assert tools == []
    assert len(findings) == 1
    assert findings[0].category == "external_scanners_skipped"
