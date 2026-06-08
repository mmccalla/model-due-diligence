"""Unit tests for the Python AST scanner."""

from __future__ import annotations

from pathlib import Path

from model_due_diligence.domain.models import RiskLevel, ScanContext, Severity
from model_due_diligence.scanners.python_ast import PythonAstScanner


def _context(target: Path, output_dir: Path) -> ScanContext:
    return ScanContext(
        target=target,
        root=target if target.is_dir() else target.parent,
        output_dir=output_dir,
        timeout_seconds=10,
        fail_on=RiskLevel.HIGH,
    )


def test_ast_scanner_flags_os_system(tmp_path: Path) -> None:
    target = tmp_path / "bad.py"
    target.write_text("import os\nos.system('echo bad')\n", encoding="utf-8")

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "python_ast_dangerous_call"
        and finding.severity == Severity.HIGH
        and finding.file == "bad.py"
        and finding.scanner == "python_ast"
        and "os.system" in finding.message
        for finding in findings
    )


def test_ast_scanner_flags_subprocess_run(tmp_path: Path) -> None:
    target = tmp_path / "subprocess_example.py"
    target.write_text("import subprocess\nsubprocess.run(['echo', 'bad'])\n", encoding="utf-8")

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "python_ast_dangerous_call"
        and finding.severity == Severity.HIGH
        and "subprocess.run" in finding.message
        for finding in findings
    )


def test_ast_scanner_flags_pickle_loads(tmp_path: Path) -> None:
    target = tmp_path / "pickle_example.py"
    target.write_text("import pickle\npickle.loads(payload)\n", encoding="utf-8")

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "python_ast_dangerous_call"
        and finding.severity == Severity.HIGH
        and "pickle.loads" in finding.message
        for finding in findings
    )


def test_ast_scanner_flags_eval_builtin(tmp_path: Path) -> None:
    target = tmp_path / "eval_example.py"
    target.write_text("eval('1 + 1')\n", encoding="utf-8")

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "python_ast_dangerous_call"
        and finding.severity == Severity.HIGH
        and "builtins.eval" in finding.message
        for finding in findings
    )


def test_ast_scanner_flags_trust_remote_code_true(tmp_path: Path) -> None:
    target = tmp_path / "remote_code.py"
    target.write_text(
        "from transformers import AutoModel\n"
        "AutoModel.from_pretrained('example/model', trust_remote_code=True)\n",
        encoding="utf-8",
    )

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "python_ast_trust_remote_code"
        and finding.severity == Severity.HIGH
        and finding.scanner == "python_ast"
        for finding in findings
    )


def test_ast_scanner_ignores_trust_remote_code_false(tmp_path: Path) -> None:
    target = tmp_path / "safe_remote_code.py"
    target.write_text(
        "from transformers import AutoModel\n"
        "AutoModel.from_pretrained('example/model', trust_remote_code=False)\n",
        encoding="utf-8",
    )

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert not any(finding.category == "python_ast_trust_remote_code" for finding in findings)


def test_ast_scanner_reports_syntax_error(tmp_path: Path) -> None:
    target = tmp_path / "broken.py"
    target.write_text("def broken(:\n", encoding="utf-8")

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert any(
        finding.category == "python_syntax_error"
        and finding.severity == Severity.MEDIUM
        and finding.file == "broken.py"
        for finding in findings
    )


def test_ast_scanner_ignores_non_python_files(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("os.system('echo bad')\n", encoding="utf-8")

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [target])

    assert findings == []


def test_ast_scanner_ignores_symlink(tmp_path: Path) -> None:
    real_file = tmp_path / "real.py"
    real_file.write_text("import os\nos.system('echo bad')\n", encoding="utf-8")
    symlink = tmp_path / "link.py"
    symlink.symlink_to(real_file)

    findings = PythonAstScanner().scan(_context(tmp_path, tmp_path / "out"), [symlink])

    assert findings == []
