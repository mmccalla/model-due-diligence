"""Quality self-check external adapters.

These adapters run the project's own quality gates as optional self-checks:
Ruff formatting, Ruff linting, Pyright and mypy. They are not model artefact
scanners. They exist to prove that the scanner project itself remains healthy.
"""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.domain.models import (
    CommandResult,
    ExternalScannerResult,
    Finding,
    ScanContext,
    Severity,
)
from model_due_diligence.external.command_runner import run_command


def scanner_project_root() -> Path:
    """Return the installed model-due-diligence repository root."""

    return Path(__file__).resolve().parents[3]


class QualitySelfCheckAdapter:
    """Run project quality self-checks against this repository."""

    def run(self, context: ScanContext) -> list[ExternalScannerResult]:
        """Run all configured quality self-checks."""

        project_root = scanner_project_root()
        targets = self._quality_targets(project_root)

        adapters = (
            self._run_ruff_format_check(context, project_root, targets),
            self._run_ruff_lint_check(context, project_root, targets),
            self._run_pyright(context, project_root),
            self._run_mypy(context, project_root, targets),
        )

        return list(adapters)

    @staticmethod
    def _quality_targets(project_root: Path) -> list[str]:
        targets: list[str] = []
        for candidate in (project_root / "src", project_root / "tests"):
            if candidate.exists():
                targets.append(str(candidate))
        return targets or [str(project_root)]

    def _run_ruff_format_check(
        self,
        context: ScanContext,
        project_root: Path,
        targets: list[str],
    ) -> ExternalScannerResult:
        result = run_command(
            tool="self_ruff_format_check",
            command=["ruff", "format", "--check", *targets],
            cwd=project_root,
            timeout_seconds=context.timeout_seconds,
        )
        return ExternalScannerResult(result, self._normalise_result(result, "Ruff format check failed."))

    def _run_ruff_lint_check(
        self,
        context: ScanContext,
        project_root: Path,
        targets: list[str],
    ) -> ExternalScannerResult:
        result = run_command(
            tool="self_ruff_check",
            command=["ruff", "check", *targets],
            cwd=project_root,
            timeout_seconds=context.timeout_seconds,
        )
        return ExternalScannerResult(result, self._normalise_result(result, "Ruff lint check failed."))

    def _run_pyright(self, context: ScanContext, project_root: Path) -> ExternalScannerResult:
        result = run_command(
            tool="self_pyright",
            command=["pyright"],
            cwd=project_root,
            timeout_seconds=context.timeout_seconds,
        )
        return ExternalScannerResult(result, self._normalise_result(result, "Pyright type check failed."))

    def _run_mypy(
        self,
        context: ScanContext,
        project_root: Path,
        targets: list[str],
    ) -> ExternalScannerResult:
        result = run_command(
            tool="self_mypy",
            command=["mypy", *targets],
            cwd=project_root,
            timeout_seconds=context.timeout_seconds,
        )
        return ExternalScannerResult(result, self._normalise_result(result, "mypy type check failed."))

    @staticmethod
    def _normalise_result(result: CommandResult, failure_message: str) -> list[Finding]:
        if not result.available:
            return [
                Finding(
                    severity=Severity.LOW,
                    category="quality_tool_unavailable",
                    file="",
                    message=f"{result.tool} is not installed or not available on PATH.",
                    recommendation=(
                        "Run ./scripts/dev-setup.sh and activate the virtual environment before running self-checks."
                    ),
                    scanner=result.tool,
                )
            ]

        if result.exit_code in (0, None):
            return []

        return [
            Finding(
                severity=Severity.LOW,
                category="quality_self_check_failed",
                file="",
                message=failure_message,
                evidence=QualitySelfCheckAdapter._evidence(result),
                recommendation="Run ./scripts/run-quality.sh --fix where appropriate, then rerun the quality gates.",
                scanner=result.tool,
            )
        ]

    @staticmethod
    def _evidence(result: CommandResult, max_length: int = 1_000) -> str | None:
        combined = "\n".join(value for value in (result.stderr.strip(), result.stdout.strip()) if value)
        if not combined:
            return None
        return combined[:max_length]
