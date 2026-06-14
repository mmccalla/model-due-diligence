"""Integration tests for Ollama scan requests through the mdd-ui API."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from tests.helpers_ollama import build_fake_ollama_store

from model_due_diligence.domain.models import AuditReport, AuditSummary, RiskLevel, ScanContext
from model_due_diligence.ollama import OllamaModel
from model_due_diligence.ui.app import API_V1_PREFIX, create_app
from model_due_diligence.ui.ollama_discovery import default_ollama_host
from model_due_diligence.ui.output_manager import ScanOutputManager
from model_due_diligence.ui.scan_service import run_scan
from model_due_diligence.ui.schemas import InteractionState


@pytest.fixture
def output_manager(tmp_path: Path) -> ScanOutputManager:
    return ScanOutputManager(root=tmp_path / "scans", max_age_seconds=0, max_dirs=2)


def _resolve_qwen3_or_raise(model_name: str) -> OllamaModel:
    if model_name != "qwen3:4b":
        raise FileNotFoundError(model_name)
    return MagicMock(spec=OllamaModel)


def _fake_ollama_runner(context: ScanContext) -> AuditReport:
    return AuditReport(
        scanned_path="ollama:qwen3:4b",
        generated_at_utc="2026-01-01T00:00:00+00:00",
        files=[],
        metadata=[],
        findings=[],
        tools=[],
        risk_score=0,
        risk_level=RiskLevel.LOW,
        summary=AuditSummary(files_scanned=1, findings=0),
    )


def test_scan_ollama_target_returns_success_with_mocked_staging(
    tmp_path: Path,
    output_manager: ScanOutputManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "staged-model"
    repo.mkdir()
    (repo / "README.md").write_text("staged ollama artefacts\n", encoding="utf-8")

    temp_dir = tempfile.TemporaryDirectory(prefix="mdd-test-ollama-")

    monkeypatch.setattr(
        "model_due_diligence.ui.scan_service.resolve_installed_model",
        _resolve_qwen3_or_raise,
    )
    monkeypatch.setattr(
        "model_due_diligence.ui.scan_service.stage_model_for_scan",
        lambda _model: (repo, temp_dir),
    )

    app = create_app(
        output_manager=output_manager,
        scan=lambda request, output_dir, scan_id: run_scan(
            request,
            output_dir,
            scan_id,
            runner=_fake_ollama_runner,
        ),
    )
    client = TestClient(app)
    response = client.post(
        f"{API_V1_PREFIX}/scan",
        json={
            "target_type": "ollama",
            "target": "qwen3:4b",
            "options": {"skip_external": False},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == InteractionState.SUCCESS.value
    assert payload["target_type"] == "ollama"
    assert payload["target"] == "qwen3:4b"
    assert payload["scanned_path"] == "ollama:qwen3:4b"
    assert payload["report"]["summary"]["files_scanned"] == 1
    assert payload["report_paths"]["scan_id"]


def test_scan_preview_ollama_target_with_mocked_staging(
    tmp_path: Path,
    output_manager: ScanOutputManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    staged = tmp_path / "preview-staged"
    staged.mkdir()
    (staged / "model.gguf").write_bytes(b"GGUF" + b"\x00" * 16)

    fake_model = MagicMock(spec=OllamaModel)
    temp_dir = tempfile.TemporaryDirectory(prefix="mdd-test-ollama-preview-")

    monkeypatch.setattr(
        "model_due_diligence.ui.scan_service.resolve_installed_model",
        lambda model_name: fake_model,
    )
    monkeypatch.setattr(
        "model_due_diligence.ui.scan_service.stage_model_for_scan",
        lambda _model: (staged, temp_dir),
    )

    app = create_app(output_manager=output_manager)
    client = TestClient(app)
    response = client.post(
        f"{API_V1_PREFIX}/scan/preview",
        json={"target_type": "ollama", "target": "llama3:8b"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == InteractionState.SUCCESS.value
    assert payload["target_type"] == "ollama"
    assert payload["items"]


def _ollama_api_available() -> bool:
    host = default_ollama_host()
    try:
        response = httpx.get(f"{host.rstrip('/')}/api/tags", timeout=1.0)
    except (httpx.HTTPError, OSError):
        return False
    return response.status_code == 200


@pytest.mark.ollama
@pytest.mark.skipif(not _ollama_api_available(), reason="Ollama API is not available")
def test_scan_ollama_target_live_when_ollama_installed(
    tmp_path: Path,
    output_manager: ScanOutputManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models_root = build_fake_ollama_store(tmp_path / "ollama-store", "qwen3:4b")
    monkeypatch.setenv("OLLAMA_MODELS", str(models_root))

    app = create_app(output_manager=output_manager)
    client = TestClient(app)
    response = client.post(
        f"{API_V1_PREFIX}/scan",
        json={
            "target_type": "ollama",
            "target": "qwen3:4b",
            "options": {"skip_external": True},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] in {
        InteractionState.SUCCESS.value,
        InteractionState.WARNING.value,
    }
    assert payload["target_type"] == "ollama"


def test_scan_ollama_missing_model_returns_404(
    tmp_path: Path,
    output_manager: ScanOutputManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models_dir = tmp_path / "empty-models"
    models_dir.mkdir()
    monkeypatch.setenv("OLLAMA_MODELS", str(models_dir))

    app = create_app(output_manager=output_manager)
    client = TestClient(app)
    response = client.post(
        f"{API_V1_PREFIX}/scan",
        json={"target_type": "ollama", "target": "missing:tag"},
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["state"] == InteractionState.ERROR.value
    assert payload["error"] == "target_not_found"
