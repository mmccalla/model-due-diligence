
"""Semgrep external scanner adapter.

Semgrep performs rule-based static analysis across source code and configuration
files. This adapter is a thin wrapper around the Semgrep CLI. Raw Semgrep JSON is
written to the output directory and high-level execution outcomes are normalised
into project findings.
"""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.config.defaults import RAW_SEMGREP_FILENAME
from model_due_diligence.domain.models import CommandResult, ExternalScannerResult, Finding, ScanContext, Severity
from model_due_diligence.external.command_runner import run_command


class SemgrepAdapter:
    """Run Semgrep against the scan target."""

    tool_name = "semgrep"

    def run(self, context: ScanContext) -> ExternalScannerResult:
        """Run Semgrep and return a normalised external scanner result.

        Semgrep findings are review signals. The raw JSON report remains the
        detailed evidence used by reviewers.
        """

        output_path = context.output_dir / RAW_SEMGREP_FILENAME
        command = self._build_command(context.target, output_path)

        result = run_command(
            tool=self.tool_name,
            command=command,
            cwd=context.root,
            timeout_seconds=context.timeout_seconds,
            output_files=[output_path],
        )

        return ExternalScannerResult(
            tool_result=result,
            findings=self._normalise_result(result),
        )

    @staticmethod
    def _build_command(target: Path, output_path: Path) -> list[str]:
        return [
            "semgrep",
            "scan",
            "--config",
            "auto",
            "--json",
            "--output",
            str(output_path),
            str(target),
        ]

    def _normalise_result(self, result: CommandResult) -> list[Finding]:
        if not result.available:
            return [
                Finding(
                    severity=Severity.LOW,
                    category="scanner_unavailable",
                    file="",
                    message="Semgrep is not installed or not available on PATH.",
                    recommendation="Install the scanner extras and rerun: python -m pip install -e '.[scanners]'",
                    scanner=self.tool_name,
                )
            ]

        if result.exit_code in (0, None):
            return []

        if result.exit_code == 1:
            return [
                Finding(
                    severity=Severity.MEDIUM,
                    category="external_scanner_findings",
                    file="",
                    message="Semgrep reported static-analysis findings. Review the raw Semgrep JSON output.",
                    evidence=self._evidence(result),
                    recommendation="Review semgrep.json and decide whether findings are expected, false positives or blocking issues.",
                    scanner=self.tool_name,
                )
            ]

        return [
            Finding(
                severity=Severity.MEDIUM,
                category="external_scanner_error",
                file="",
                message=f"Semgrep exited with unexpected code {result.exit_code}.",
                evidence=self._evidence(result),
                recommendation="Review stderr/stdout and rerun Semgrep manually if needed.",
                scanner=self.tool_name,
            )
        ]

    @staticmethod
    def _evidence(result: CommandResult, max_length: int = 1_000) -> str | None:
        combined = "\n".join(value for value in (result.stderr.strip(), result.stdout.strip()) if value)
        if not combined:
            return None
        return combined[:max_length]
