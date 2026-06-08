from pathlib import Path
from model_due_diligence.domain.models import ScanContext
from model_due_diligence.scanners.model_metadata import ModelMetadataScanner


def test_gguf_metadata(tmp_path: Path) -> None:
    target = tmp_path / "x.gguf"
    target.write_bytes(b"GGUF" + b"\x03\x00\x00\x00")
    ctx = ScanContext(target, tmp_path, tmp_path / "out", 10)
    metadata, _ = ModelMetadataScanner().scan(ctx, [target])
    assert metadata[0].metadata["magic"] == "GGUF"
