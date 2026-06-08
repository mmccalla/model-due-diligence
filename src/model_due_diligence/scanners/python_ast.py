from __future__ import annotations

import ast
from pathlib import Path
from collections.abc import Iterable

from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.utils import read_text_safely, safe_relative


class PythonAstScanner:
    DANGEROUS_CALLS = {("os", "system"), ("subprocess", "run"), ("subprocess", "Popen"), ("pickle", "load"), ("pickle", "loads"), ("marshal", "loads"), ("builtins", "eval"), ("builtins", "exec")}

    def scan(self, context: ScanContext, files: Iterable[Path]) -> list[Finding]:
        findings: list[Finding] = []
        for path in files:
            if path.suffix.lower() != ".py" or path.is_symlink():
                continue
            text = read_text_safely(path)
            if text is None:
                continue
            relative = safe_relative(path, context.root)
            try:
                tree = ast.parse(text, filename=relative)
            except SyntaxError as exc:
                findings.append(Finding(Severity.MEDIUM, "python_syntax_error", relative, f"Python syntax error: {exc}"))
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    call_name = self._resolve_call_name(node.func)
                    if call_name in self.DANGEROUS_CALLS:
                        findings.append(Finding(Severity.HIGH, "python_ast_dangerous_call", relative, f"Dangerous call detected: {'.'.join(call_name)}", evidence=f"line={getattr(node, 'lineno', '?')}", recommendation="Review whether this can execute during import/model loading."))
        return findings

    @staticmethod
    def _resolve_call_name(func: ast.AST) -> tuple[str, str] | tuple[()]:
        if isinstance(func, ast.Name):
            return ("builtins", func.id)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return (func.value.id, func.attr)
        return ()
