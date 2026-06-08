
"""pip-audit external scanner adapter.

`pip-audit` identifies known vulnerabilities in Python dependency files. This
adapter scans discovered requirements files and preserves raw pip-audit JSON
outputs in the report directory. It normalises only high-level execution outcomes
into project findings.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from model_due_diligence.config.defaults import DEPENDENCY_FILE_NAMES
from model_due_diligence.domain.models import CommandResult, ExternalScannerResult, Finding, ScanContext, Severity
from model_due_diligence.external.command_runner import run_command


class PipAuditAdapter:
    """Run pip-audit against supported Python dependency files."""

    tool_name = "pip-audit"

    def run(self, context: ScanContext) -> list[ExternalScannerResult]:
        """Run pip-audit for each supported requirements file found."""

        dependency_files = self._find_dependency_files(context)

        if not dependency_files:
            return []

        results: list[ExternalScannerResult] = []
        for dependency_file in dependency_files:
            output_path = self._output_path(context.output_dir, dependency_file)
            command = self._build_command(dependency_file, output_path)

            result = run_command(
                tool=self.tool_name,
                command=command,
                cwd=context.root,
                timeout_seconds=context.timeout_seconds,
                output_files=[output_path],
            )

            results.append(
                ExternalScannerResult(
                    tool_result=result,
                    findings=self._normalise_result(result, dependency_file),
                )
            )

        return results

    @staticmethod
    def _find_dependency_files(context: ScanContext) -> list[Path]:
        if context.target.is_file():
            return [context.target] if context.target.name in DEPENDENCY_FILE_NAMES else []

        return sorted(
            path
            for path in context.target.rglob("*")
            if path.is_file() and path.name in DEPENDENCY_FILE_NAMES and path.name == "requirements.txt"
        )

    @staticmethod
    def _output_path(output_dir: Path, dependency_file: Path) -> Path:
        digest = hashlib.sha256(str(dependency_file).encode("utf-8")).hexdigest()[:12]
        return output_dir / f"pip-audit-{digest}.json"

    @staticmethod
    def _build_command(dependency_file: Path, output_path: Path) -> list[str]:
        return [
            "pip-audit",
            "-r",
            str(dependency_file),
            "-f",
            "json",
            "-o",
            str(output_path),
        ]

    def _normalise_result(self, result: CommandResult, dependency_file: Path) -> list[Finding]:
        file_path = str(dependency_file)

        if not result.available:
            return [
                Finding(
                    severity=Severity.LOW,
                    category="scanner_unavailable",
                    file=file_path,
                    message="pip-audit is not installed or not available on PATH.",
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
                    file=file_path,
                    message="pip-audit reported known vulnerabilities in a Python dependency file.",
                    evidence=self._evidence(result),
                    recommendation="Review the raw pip-audit JSON output and update or justify vulnerable dependencies.",
                    scanner=self.tool_name,
                )
            ]

        return [
            Finding(
                severity=Severity.MEDIUM,
                category="external_scanner_error",
                file=file_path,
                message=f"pip-audit exited with unexpected code {result.exit_code}.",
                evidence=self._evidence(result),
                recommendation="Review stderr/stdout and rerun pip-audit manually if needed.",
                scanner=self.tool_name,
            )
        ]

    @staticmethod
    def _evidence(result: CommandResult, max_length: int = 1_000) -> str | None:
        combined = "\n".join(value for value in (result.stderr.strip(), result.stdout.strip()) if value)
        if not combined:
            return None
        return combined[:max_length]
