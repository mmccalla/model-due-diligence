from pathlib import Path
from model_due_diligence.domain.models import ScanContext
from model_due_diligence.scanners.python_ast import PythonAstScanner


def test_ast_scanner_flags_os_system(tmp_path: Path) -> None:
    target = tmp_path / "bad.py"
    target.write_text("import os\nos.system('echo bad')\n")
    ctx = ScanContext(tmp_path, tmp_path, tmp_path / "out", 10)
    findings = PythonAstScanner().scan(ctx, [target])
    assert findings
