"""External scanner orchestration.

This module coordinates optional external scanner adapters and normalises their
outputs into the domain model expected by the application layer.

Individual adapters own command construction and high-level result mapping. The
runner only decides which adapters should run based on `ScanContext` flags and
then flattens their results into `CommandResult[]` and `Finding[]`.
"""

from __future__ import annotations

from collections.abc import Iterable

from model_due_diligence.domain.models import CommandResult, ExternalScannerResult, Finding, ScanContext, Severity
from model_due_diligence.external.bandit import BanditAdapter
from model_due_diligence.external.detect_secrets import DetectSecretsAdapter
from model_due_diligence.external.modelscan import ModelScanAdapter
from model_due_diligence.external.pip_audit import PipAuditAdapter
from model_due_diligence.external.quality import QualitySelfCheckAdapter
from model_due_diligence.external.semgrep import SemgrepAdapter


class ExternalScannerRunner:
    """Run all enabled external scanners for a scan context."""

    def __init__(
        self,
        modelscan: ModelScanAdapter | None = None,
        semgrep: SemgrepAdapter | None = None,
        bandit: BanditAdapter | None = None,
        pip_audit: PipAuditAdapter | None = None,
        detect_secrets: DetectSecretsAdapter | None = None,
        quality: QualitySelfCheckAdapter | None = None,
    ) -> None:
        self._modelscan = modelscan or ModelScanAdapter()
        self._semgrep = semgrep or SemgrepAdapter()
        self._bandit = bandit or BanditAdapter()
        self._pip_audit = pip_audit or PipAuditAdapter()
        self._detect_secrets = detect_secrets or DetectSecretsAdapter()
        self._quality = quality or QualitySelfCheckAdapter()

    def run_all(self, context: ScanContext) -> tuple[list[CommandResult], list[Finding]]:
        """Run enabled external scanners and return command results plus findings."""

        if context.skip_external:
            return [], [self._external_scanners_skipped_finding()]

        scanner_results = list(self._run_enabled_scanners(context))
        command_results = [result.tool_result for result in scanner_results]
        findings = [finding for result in scanner_results for finding in result.findings]

        return command_results, findings

    def _run_enabled_scanners(self, context: ScanContext) -> Iterable[ExternalScannerResult]:
        if not context.skip_modelscan:
            yield self._modelscan.run(context)

        if not context.skip_semgrep:
            yield self._semgrep.run(context)

        if not context.skip_bandit:
            yield self._bandit.run(context)

        if not context.skip_pip_audit:
            yield from self._pip_audit.run(context)

        if not context.skip_detect_secrets:
            yield self._detect_secrets.run(context)

        if context.quality_self_check and not context.skip_quality_self_check:
            yield from self._quality.run(context)

    @staticmethod
    def _external_scanners_skipped_finding() -> Finding:
        return Finding(
            severity=Severity.LOW,
            category="external_scanners_skipped",
            file="",
            message="External scanners were skipped by CLI option.",
            recommendation="Rerun without --skip-external for fuller supply-chain due diligence.",
            scanner="external_scanner_runner",
        )
