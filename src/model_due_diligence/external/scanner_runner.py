from __future__ import annotations

import hashlib
from pathlib import Path

from model_due_diligence.domain.models import CommandResult, Finding, ScanContext, Severity
from model_due_diligence.external.command_runner import run_command


class ExternalScannerRunner:
    def run_all(self, context: ScanContext) -> tuple[list[CommandResult], list[Finding]]:
        if context.skip_external:
            return [], [Finding(Severity.LOW, "external_scanners_skipped", "", "External scanners were skipped by CLI option.")]
        results: list[CommandResult] = []
        if not context.skip_modelscan: results.append(self._run_modelscan(context))
        if not context.skip_semgrep: results.append(self._run_semgrep(context))
        if not context.skip_bandit: results.append(self._run_bandit(context))
        if not context.skip_pip_audit: results.extend(self._run_pip_audit(context))
        if not context.skip_detect_secrets: results.append(self._run_detect_secrets(context))
        if context.quality_self_check and not context.skip_quality_self_check: results.extend(self._run_quality_self_check(context))
        findings = [Finding(Severity.LOW, "scanner_unavailable", "", f"{r.tool} is not installed or not available on PATH.") for r in results if not r.available]
        return results, findings

    @staticmethod
    def _run_modelscan(context: ScanContext) -> CommandResult:
        output = context.output_dir / "modelscan.json"
        return run_command("modelscan", ["modelscan", "-p", str(context.target), "-r", "json", "-o", str(output), "--show-skipped"], context.root, context.timeout_seconds, [output])

    @staticmethod
    def _run_semgrep(context: ScanContext) -> CommandResult:
        output = context.output_dir / "semgrep.json"
        return run_command("semgrep", ["semgrep", "scan", "--config", "auto", "--json", "--output", str(output), str(context.target)], context.root, context.timeout_seconds, [output])

    @staticmethod
    def _run_bandit(context: ScanContext) -> CommandResult:
        output = context.output_dir / "bandit.json"
        return run_command("bandit", ["bandit", "-r", str(context.target), "-f", "json", "-o", str(output)], context.root, context.timeout_seconds, [output])

    @staticmethod
    def _run_pip_audit(context: ScanContext) -> list[CommandResult]:
        results: list[CommandResult] = []
        for req in context.root.rglob("requirements.txt") if context.root.is_dir() else []:
            output = context.output_dir / f"pip-audit-{hashlib.sha256(str(req).encode()).hexdigest()[:12]}.json"
            results.append(run_command("pip-audit", ["pip-audit", "-r", str(req), "-f", "json", "-o", str(output)], context.root, context.timeout_seconds, [output]))
        return results

    @staticmethod
    def _run_detect_secrets(context: ScanContext) -> CommandResult:
        output = context.output_dir / "detect-secrets.json"
        result = run_command("detect-secrets", ["detect-secrets", "scan", str(context.target), "--all-files"], context.root, context.timeout_seconds)
        if result.available:
            output.write_text(result.stdout, encoding="utf-8")
        return CommandResult(result.tool, result.available, result.command, result.exit_code, result.stdout, result.stderr, [str(output)])

    @staticmethod
    def _run_quality_self_check(context: ScanContext) -> list[CommandResult]:
        script_root = Path(__file__).resolve().parents[2]
        return [
            run_command("self_ruff_check", ["ruff", "check", str(script_root)], script_root, context.timeout_seconds),
            run_command("self_ruff_format_check", ["ruff", "format", "--check", str(script_root)], script_root, context.timeout_seconds),
            run_command("self_pyright", ["pyright", str(script_root), "--outputjson"], script_root, context.timeout_seconds),
            run_command("self_mypy", ["mypy", str(script_root)], script_root, context.timeout_seconds),
        ]
