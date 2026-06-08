from pathlib import Path
from model_due_diligence.domain.models import ScanContext
from model_due_diligence.inventory.file_inventory import FileInventoryBuilder


def test_inventory_builds_hash(tmp_path: Path) -> None:
    target = tmp_path / "model.gguf"
    target.write_bytes(b"GGUF" + b"\x03\x00\x00\x00")
    ctx = ScanContext(target, tmp_path, tmp_path / "out", 10)
    records, _ = FileInventoryBuilder().build(ctx)
    assert len(records) == 1
    assert records[0].sha256 != ""
