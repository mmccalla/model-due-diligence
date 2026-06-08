"""detect-secrets external scanner adapter.

`detect-secrets` identifies committed secrets and credential-like values. This
adapter is a thin wrapper around the CLI. Raw detect-secrets JSON is written to
the output directory and only high-level execution outcomes are normalised into
project findings.
"""

from __future__ import annotations

from model_due_diligence.config.defaults import RAW_DETECT_SECRETS_FILENAME
from model_due_diligence.domain.models import CommandResult, ExternalScannerResult, Finding, ScanContext, Severity
from model_due_diligence.external.command_runner import run_command


class DetectSecretsAdapter:
    """Run detect-secrets against the scan target."""

    tool_name = "detect-secrets"

    def run(self, context: ScanContext) -> ExternalScannerResult:
        """Run detect-secrets and return a normalised external scanner result."""

        output_path = context.output_dir / RAW_DETECT_SECRETS_FILENAME
        command = self._build_command(context.target)

        result = run_command(
            tool=self.tool_name,
            command=command,
            cwd=context.root,
            timeout_seconds=context.timeout_seconds,
        )

        if result.available:
            self._write_stdout_report(result, output_path)
            result = CommandResult(
                tool=result.tool,
                available=result.available,
                command=result.command,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                output_files=[str(output_path)],
                duration_seconds=result.duration_seconds,
            )

        return ExternalScannerResult(
            tool_result=result,
            findings=self._normalise_result(result),
        )

    @staticmethod
    def _build_command(target: object) -> list[str]:
        return [
            "detect-secrets",
            "scan",
            str(target),
            "--all-files",
        ]

    @staticmethod
    def _write_stdout_report(result: CommandResult, output_path: object) -> None:
        try:
            output_path.write_text(result.stdout, encoding="utf-8")  # type: ignore[attr-defined]
        except OSError:
            # The command result still carries stdout/stderr evidence. Report writing
            # failure should not mask the scanner execution result.
            return

    def _normalise_result(self, result: CommandResult) -> list[Finding]:
        if not result.available:
            return [
                Finding(
                    severity=Severity.LOW,
                    category="scanner_unavailable",
                    file="",
                    message="detect-secrets is not installed or not available on PATH.",
                    recommendation="Install the scanner extras and rerun: python -m pip install -e '.[scanners]'",
                    scanner=self.tool_name,
                )
            ]

        if result.exit_code in (0, None):
            if self._stdout_contains_potential_secrets(result.stdout):
                return [
                    Finding(
                        severity=Severity.MEDIUM,
                        category="external_scanner_findings",
                        file="",
                        message="detect-secrets reported potential secrets. Review the raw detect-secrets JSON output.",
                        evidence=self._evidence(result),
                        recommendation=(
                            "Review detect-secrets.json. If any real credentials are present, remove them "
                            "and rotate them."
                        ),
                        scanner=self.tool_name,
                    )
                ]
            return []

        return [
            Finding(
                severity=Severity.MEDIUM,
                category="external_scanner_error",
                file="",
                message=f"detect-secrets exited with unexpected code {result.exit_code}.",
                evidence=self._evidence(result),
                recommendation="Review stderr/stdout and rerun detect-secrets manually if needed.",
                scanner=self.tool_name,
            )
        ]

    @staticmethod
    def _stdout_contains_potential_secrets(stdout: str) -> bool:
        # detect-secrets emits a JSON baseline where an empty `results` object
        # means no potential secrets were found.
        compact = stdout.replace(" ", "").replace("\n", "")
        return '"results":{}' not in compact and '"results":' in compact

    @staticmethod
    def _evidence(result: CommandResult, max_length: int = 1_000) -> str | None:
        combined = "\n".join(value for value in (result.stderr.strip(), result.stdout.strip()) if value)
        if not combined:
            return None
        return combined[:max_length]
