from pathlib import Path
from model_due_diligence.cli import main


def test_cli_smoke_skip_external(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello")
    code = main([str(repo), "--out", str(tmp_path / "audit"), "--skip-external", "--fail-on", "critical"])
    assert code == 0
    assert (tmp_path / "audit" / "model_due_diligence_report.md").exists()
