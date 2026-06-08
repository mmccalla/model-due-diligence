"""Python AST scanner.

This scanner performs lightweight static analysis of Python files without
executing or importing them. It detects dangerous calls that may execute shell
commands, deserialize unsafe payloads, dynamically evaluate code or remove files.

Findings are review signals, not proof of compromise.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

from model_due_diligence.config.suspicious_patterns import PYTHON_DANGEROUS_CALLS
from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import read_text_safely, safe_relative


class PythonAstScanner:
    """Scan Python source files for dangerous AST call patterns."""

    scanner_name = "python_ast"

    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        """Return findings for dangerous Python call patterns."""

        findings: list[Finding] = []

        for path in files:
            if self._should_skip(path):
                continue

            text = read_text_safely(path)
            if text is None:
                continue

            relative = safe_relative(path, context.root)
            tree = self._parse_python(relative, text, findings)
            if tree is None:
                continue

            findings.extend(self._scan_tree(relative, tree))

        return findings

    @staticmethod
    def _should_skip(path: Path) -> bool:
        return path.is_symlink() or path.suffix.lower() != ".py"

    def _parse_python(self, relative: str, text: str, findings: list[Finding]) -> ast.AST | None:
        try:
            return ast.parse(text, filename=relative)
        except SyntaxError as exc:
            findings.append(self._syntax_error_finding(relative, exc))
            return None

    def _scan_tree(self, relative: str, tree: ast.AST) -> list[Finding]:
        findings: list[Finding] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            call_name = self._resolve_call_name(node.func)
            if call_name in PYTHON_DANGEROUS_CALLS:
                findings.append(self._dangerous_call_finding(relative, call_name, node))

            if self._is_transformers_remote_code_enabled(node):
                findings.append(self._trust_remote_code_finding(relative, node))

        return findings

    def _syntax_error_finding(self, relative: str, exc: SyntaxError) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="python_syntax_error",
            file=relative,
            message=f"Python syntax error: {exc}",
            recommendation="Review manually. Malformed Python may also avoid some static checks.",
            scanner=self.scanner_name,
        )

    def _dangerous_call_finding(self, relative: str, call_name: tuple[str, str], node: ast.Call) -> Finding:
        return Finding(
            severity=Severity.HIGH,
            category="python_ast_dangerous_call",
            file=relative,
            message=f"Dangerous call detected: {'.'.join(call_name)}.",
            evidence=f"line={getattr(node, 'lineno', '?')}",
            recommendation="Review whether this call can execute during import, setup or model loading.",
            scanner=self.scanner_name,
        )

    def _trust_remote_code_finding(self, relative: str, node: ast.Call) -> Finding:
        return Finding(
            severity=Severity.HIGH,
            category="python_ast_trust_remote_code",
            file=relative,
            message="Transformers call enables trust_remote_code=True.",
            evidence=f"line={getattr(node, 'lineno', '?')}",
            recommendation=(
                "Avoid trust_remote_code=True unless the repository code has been manually reviewed and the source "
                "is trusted. Treat it as executable code."
            ),
            scanner=self.scanner_name,
        )

    @staticmethod
    def _resolve_call_name(func: ast.AST) -> tuple[str, str] | tuple[()]:
        if isinstance(func, ast.Name):
            return ("builtins", func.id)

        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return (func.value.id, func.attr)

        return ()

    @staticmethod
    def _is_transformers_remote_code_enabled(node: ast.Call) -> bool:
        return any(
            keyword.arg == "trust_remote_code"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in node.keywords
        )
