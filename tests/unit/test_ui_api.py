"""API tests for the mdd-ui dashboard backend."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from model_due_diligence.domain.models import RiskLevel
from model_due_diligence.ui.app import create_app
from model_due_diligence.ui.schemas import (
    InteractionState,
    OllamaDiscoverySource,
    OllamaModelsResponse,
    OllamaModelSummary,
    OllamaStatusResponse,
    ScanPreviewItem,
    ScanPreviewResponse,
    ScanReportPaths,
    ScanResponse,
)


@pytest.fixture
def client() -> TestClient:
    app = create_app(
        get_status=lambda: OllamaStatusResponse(
            state=InteractionState.SUCCESS,
            source=OllamaDiscoverySource.API,
            host="http://127.0.0.1:11434",
            connected=True,
            message="Connected to Ollama server.",
        ),
        list_models=lambda: OllamaModelsResponse(
            state=InteractionState.SUCCESS,
            source=OllamaDiscoverySource.API,
            host="http://127.0.0.1:11434",
            models=[
                OllamaModelSummary(
                    name="llama3:8b",
                    source=OllamaDiscoverySource.API,
                    size_bytes=100,
                )
            ],
            message="Discovered 1 installed model(s) from Ollama API.",
        ),
        preview=lambda request: ScanPreviewResponse(
            state=InteractionState.SUCCESS,
            target_type=request.target_type,
            target=request.target,
            resolved_path="/tmp/preview",
            items=[ScanPreviewItem(label="model.gguf", path="/tmp/preview/model.gguf", kind="gguf")],
            message="Ready to inspect.",
        ),
        scan=lambda request, output_dir: ScanResponse(
            state=InteractionState.SUCCESS,
            target_type=request.target_type,
            target=request.target,
            scanned_path=request.target,
            report={
                "risk_level": RiskLevel.LOW.value,
                "risk_score": 0,
                "summary": {"findings": 0},
            },
            report_paths=ScanReportPaths(
                markdown_path=str(output_dir / "model_due_diligence_report.md"),
                json_path=str(output_dir / "model_due_diligence_report.json"),
                sarif_path=str(output_dir / "model_due_diligence_report.sarif"),
                output_dir=str(output_dir),
            ),
            message="Static scan completed.",
        ),
    )
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "mdd-ui"


def test_ollama_status_endpoint(client: TestClient) -> None:
    response = client.get("/api/ollama/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == InteractionState.SUCCESS.value
    assert payload["connected"] is True


def test_ollama_models_endpoint(client: TestClient) -> None:
    response = client.get("/api/ollama/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["models"][0]["name"] == "llama3:8b"


def test_scan_preview_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/scan/preview",
        json={"target_type": "path", "target": "/tmp/example.gguf"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == InteractionState.SUCCESS.value
    assert payload["items"][0]["kind"] == "gguf"


def test_scan_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/scan",
        json={"target_type": "path", "target": "/tmp/example.gguf"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == InteractionState.SUCCESS.value
    assert payload["report"]["risk_level"] == RiskLevel.LOW.value


def test_scan_preview_path_integration(tmp_path: Path) -> None:
    target = tmp_path / "demo.gguf"
    target.write_bytes(b"GGUF" + b"\x00" * 16)

    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/api/scan/preview",
        json={"target_type": "path", "target": str(target)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == InteractionState.SUCCESS.value
    assert payload["items"]


def test_scan_path_integration(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello\n", encoding="utf-8")

    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/api/scan",
        json={
            "target_type": "path",
            "target": str(repo),
            "options": {"skip_external": True},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == InteractionState.SUCCESS.value
    assert payload["report"]["summary"]["files_scanned"] == 1


def test_scan_missing_target_returns_404(tmp_path: Path) -> None:
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/api/scan",
        json={"target_type": "path", "target": str(tmp_path / "missing")},
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["state"] == InteractionState.ERROR.value
