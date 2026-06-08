"""Bandit external scanner adapter.

Bandit performs Python-focused static security analysis. This adapter is a thin
wrapper around the Bandit CLI and deliberately avoids interpreting Bandit
findings in detail. Raw Bandit JSON is written to the output directory and the
normalised finding model records only tool availability and execution signals.
"""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.config.defaults import RAW_BANDIT_FILENAME
from model_due_diligence.domain.models import CommandResult, ExternalScannerResult, Finding, ScanContext, Severity
from model_due_diligence.external.command_runner import run_command


class BanditAdapter:
    """Run Bandit against the scan target."""

    tool_name = "bandit"

    def run(self, context: ScanContext) -> ExternalScannerResult:
        """Run Bandit and return a normalised external scanner result."""

        output_path = context.output_dir / RAW_BANDIT_FILENAME
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
            "bandit",
            "-r",
            str(target),
            "-f",
            "json",
            "-o",
            str(output_path),
        ]

    def _normalise_result(self, result: CommandResult) -> list[Finding]:
        if not result.available:
            return [
                Finding(
                    severity=Severity.LOW,
                    category="scanner_unavailable",
                    file="",
                    message="Bandit is not installed or not available on PATH.",
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
                    message="Bandit reported Python security findings. Review the raw Bandit JSON output.",
                    evidence=self._evidence(result),
                    recommendation=(
                        "Review bandit.json and decide whether findings are expected, false positives "
                        "or blocking issues."
                    ),
                    scanner=self.tool_name,
                )
            ]

        return [
            Finding(
                severity=Severity.MEDIUM,
                category="external_scanner_error",
                file="",
                message=f"Bandit exited with unexpected code {result.exit_code}.",
                evidence=self._evidence(result),
                recommendation="Review stderr/stdout and rerun Bandit manually if needed.",
                scanner=self.tool_name,
            )
        ]

    @staticmethod
    def _evidence(result: CommandResult, max_length: int = 1_000) -> str | None:
        combined = "\n".join(value for value in (result.stderr.strip(), result.stdout.strip()) if value)
        if not combined:
            return None
        return combined[:max_length]
