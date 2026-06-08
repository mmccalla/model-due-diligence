from __future__ import annotations

from collections import Counter
from typing import Any

from model_due_diligence.domain.models import AuditReport, FileRecord, Finding, ScanContext, Severity
from model_due_diligence.domain.risk import RiskScorer
from model_due_diligence.external.scanner_runner import ExternalScannerRunner
from model_due_diligence.inventory.file_inventory import FileInventoryBuilder
from model_due_diligence.scanners.binary_strings import BinaryStringScanner
from model_due_diligence.scanners.entropy import EntropyScanner
from model_due_diligence.scanners.git_provenance import GitProvenanceScanner
from model_due_diligence.scanners.model_metadata import ModelMetadataScanner
from model_due_diligence.scanners.pickle_heuristics import PickleHeuristicScanner
from model_due_diligence.scanners.python_ast import PythonAstScanner
from model_due_diligence.scanners.text_patterns import SuspiciousTextScanner
from model_due_diligence.utils import iter_files, utc_now_iso


class ModelDueDiligenceApp:
    def __init__(self) -> None:
        self.inventory = FileInventoryBuilder()
        self.text_scanner = SuspiciousTextScanner()
        self.ast_scanner = PythonAstScanner()
        self.binary_scanner = BinaryStringScanner()
        self.entropy_scanner = EntropyScanner()
        self.git_scanner = GitProvenanceScanner()
        self.metadata_scanner = ModelMetadataScanner()
        self.pickle_scanner = PickleHeuristicScanner()
        self.external_scanners = ExternalScannerRunner()
        self.risk_scorer = RiskScorer()

    def run(self, context: ScanContext) -> AuditReport:
        context.output_dir.mkdir(parents=True, exist_ok=True)
        files = iter_files(context.target)
        records, findings = self.inventory.build(context)
        findings.extend(self.text_scanner.scan(context, files))
        findings.extend(self.ast_scanner.scan(context, files))
        findings.extend(self.binary_scanner.scan(context, files))
        findings.extend(self.entropy_scanner.scan(context, files))
        findings.extend(self.pickle_scanner.scan(context, files))
        git_findings, git_metadata = self.git_scanner.scan(context); findings.extend(git_findings)
        model_metadata, metadata_findings = self.metadata_scanner.scan(context, files); findings.extend(metadata_findings)
        tools, tool_findings = self.external_scanners.run_all(context); findings.extend(tool_findings)
        score, level = self.risk_scorer.score(findings, tools)
        return AuditReport(str(context.target), utc_now_iso(), records, model_metadata, findings, tools, score, level, self._build_summary(records, findings, git_metadata, len(tools)))

    @staticmethod
    def _build_summary(records: list[FileRecord], findings: list[Finding], git_metadata: dict[str, Any], tool_count: int) -> dict[str, Any]:
        severity_counts = Counter(f.severity.value for f in findings)
        category_counts = Counter(r.category for r in records)
        return {
            "files_scanned": len(records),
            "findings": len(findings),
            "critical_findings": severity_counts.get(Severity.CRITICAL.value, 0),
            "high_findings": severity_counts.get(Severity.HIGH.value, 0),
            "medium_findings": severity_counts.get(Severity.MEDIUM.value, 0),
            "low_findings": severity_counts.get(Severity.LOW.value, 0),
            "info_findings": severity_counts.get(Severity.INFO.value, 0),
            "file_categories": dict(category_counts),
            "external_tools_run": tool_count,
            "git": git_metadata,
        }

"""Application orchestration for model-due-diligence.

The app layer coordinates inventory, native scanners, external scanners, risk
scoring and report-model construction. Scanner-specific rules live in scanner
modules; reporting logic lives in reporting modules.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from model_due_diligence.domain.models import AuditReport, AuditSummary, FileCategory, FileRecord, Finding, ScanContext
from model_due_diligence.domain.risk import RiskScorer
from model_due_diligence.external.scanner_runner import ExternalScannerRunner
from model_due_diligence.inventory.file_inventory import FileInventoryBuilder
from model_due_diligence.scanners.binary_strings import BinaryStringScanner
from model_due_diligence.scanners.entropy import EntropyScanner
from model_due_diligence.scanners.git_provenance import GitProvenanceScanner
from model_due_diligence.scanners.model_metadata import ModelMetadataScanner
from model_due_diligence.scanners.pickle_heuristics import PickleHeuristicScanner
from model_due_diligence.scanners.python_ast import PythonAstScanner
from model_due_diligence.scanners.text_patterns import SuspiciousTextScanner
from model_due_diligence.utils import iter_files, utc_now_iso


class ModelDueDiligenceApp:
    """Coordinate a complete static due-diligence scan."""

    def __init__(
        self,
        inventory: FileInventoryBuilder | None = None,
        text_scanner: SuspiciousTextScanner | None = None,
        ast_scanner: PythonAstScanner | None = None,
        binary_scanner: BinaryStringScanner | None = None,
        entropy_scanner: EntropyScanner | None = None,
        git_scanner: GitProvenanceScanner | None = None,
        metadata_scanner: ModelMetadataScanner | None = None,
        pickle_scanner: PickleHeuristicScanner | None = None,
        external_scanners: ExternalScannerRunner | None = None,
        risk_scorer: RiskScorer | None = None,
    ) -> None:
        self.inventory = inventory or FileInventoryBuilder()
        self.text_scanner = text_scanner or SuspiciousTextScanner()
        self.ast_scanner = ast_scanner or PythonAstScanner()
        self.binary_scanner = binary_scanner or BinaryStringScanner()
        self.entropy_scanner = entropy_scanner or EntropyScanner()
        self.git_scanner = git_scanner or GitProvenanceScanner()
        self.metadata_scanner = metadata_scanner or ModelMetadataScanner()
        self.pickle_scanner = pickle_scanner or PickleHeuristicScanner()
        self.external_scanners = external_scanners or ExternalScannerRunner()
        self.risk_scorer = risk_scorer or RiskScorer()

    def run(self, context: ScanContext) -> AuditReport:
        """Run a complete scan and return an audit report domain object."""

        context.output_dir.mkdir(parents=True, exist_ok=True)

        files = iter_files(context.target)
        records, findings = self.inventory.build(context)

        findings.extend(self._run_native_finding_scanners(context, files))

        git_findings, git_metadata = self.git_scanner.scan(context)
        findings.extend(git_findings)

        model_metadata, metadata_findings = self.metadata_scanner.scan(context, files)
        findings.extend(metadata_findings)

        tools, tool_findings = self.external_scanners.run_all(context)
        findings.extend(tool_findings)

        risk_score, risk_level = self.risk_scorer.score(findings, tools)

        return AuditReport(
            scanned_path=str(context.target),
            generated_at_utc=utc_now_iso(),
            files=records,
            metadata=model_metadata,
            findings=findings,
            tools=tools,
            risk_score=risk_score,
            risk_level=risk_level,
            summary=self._build_summary(
                records=records,
                findings=findings,
                git_metadata=git_metadata,
                tool_count=len(tools),
            ),
        )

    def _run_native_finding_scanners(self, context: ScanContext, files: list[Any]) -> list[Finding]:
        """Run native scanners that return findings only."""

        findings: list[Finding] = []

        findings.extend(self.text_scanner.scan(context, files))
        findings.extend(self.ast_scanner.scan(context, files))
        findings.extend(self.binary_scanner.scan(context, files))
        findings.extend(self.entropy_scanner.scan(context, files))
        findings.extend(self.pickle_scanner.scan(context, files))

        return findings

    @staticmethod
    def _build_summary(
        records: list[FileRecord],
        findings: list[Finding],
        git_metadata: dict[str, Any],
        tool_count: int,
    ) -> AuditSummary:
        severity_counts = Counter(finding.severity for finding in findings)
        category_counts = Counter(_file_category_value(record.category) for record in records)

        return AuditSummary(
            files_scanned=len(records),
            findings=len(findings),
            critical_findings=severity_counts.get(findings[0].severity.CRITICAL, 0) if findings else 0,
            high_findings=severity_counts.get(findings[0].severity.HIGH, 0) if findings else 0,
            medium_findings=severity_counts.get(findings[0].severity.MEDIUM, 0) if findings else 0,
            low_findings=severity_counts.get(findings[0].severity.LOW, 0) if findings else 0,
            info_findings=severity_counts.get(findings[0].severity.INFO, 0) if findings else 0,
            external_tools_run=tool_count,
            file_categories=dict(category_counts),
            git=git_metadata,
        )


def _file_category_value(category: FileCategory | str) -> str:
    if isinstance(category, FileCategory):
        return category.value
    return category