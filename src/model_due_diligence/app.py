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
