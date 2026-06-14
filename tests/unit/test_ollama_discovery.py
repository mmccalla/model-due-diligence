"""Unit tests for Ollama model discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tests.helpers_ollama import build_fake_ollama_store

from model_due_diligence.ui.ollama_discovery import (
    OllamaDiscoverySettings,
    get_ollama_status,
    list_ollama_models,
)
from model_due_diligence.ui.schemas import InteractionState, OllamaDiscoverySource


@dataclass
class FakeResponse:
    status_code: int
    payload: dict[str, object]

    def json(self) -> dict[str, object]:
        return self.payload


@dataclass
class FakeClient:
    response: FakeResponse | None
    error: Exception | None = None
    url: str | None = None

    def get(self, url: str, *, timeout: float) -> FakeResponse:
        _ = timeout
        self.url = url
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def test_get_ollama_status_reports_api_connection() -> None:
    client = FakeClient(
        response=FakeResponse(status_code=200, payload={"models": []}),
    )
    settings = OllamaDiscoverySettings(host="http://127.0.0.1:11434", models_dir=Path("/tmp/unused"))

    status = get_ollama_status(settings, client=client)

    assert status.state == InteractionState.SUCCESS
    assert status.source == OllamaDiscoverySource.API
    assert status.connected is True
    assert client.url == "http://127.0.0.1:11434/api/tags"


def test_list_ollama_models_uses_api_when_available() -> None:
    client = FakeClient(
        response=FakeResponse(
            status_code=200,
            payload={
                "models": [
                    {
                        "name": "llama3:8b",
                        "size": 1234,
                        "digest": "sha256:abc",
                        "modified_at": "2026-01-01T00:00:00Z",
                        "details": {"family": "llama"},
                    }
                ]
            },
        ),
    )
    settings = OllamaDiscoverySettings(host="http://127.0.0.1:11434", models_dir=Path("/tmp/unused"))

    response = list_ollama_models(settings, client=client)

    assert response.state == InteractionState.SUCCESS
    assert response.source == OllamaDiscoverySource.API
    assert response.models[0].name == "llama3:8b"
    assert response.models[0].family == "llama"


def test_list_ollama_models_falls_back_to_filesystem(tmp_path: Path) -> None:
    models_dir = build_fake_ollama_store(tmp_path, "qwen3:4b")
    client = FakeClient(response=None, error=ConnectionError("offline"))
    settings = OllamaDiscoverySettings(host="http://127.0.0.1:11434", models_dir=models_dir)

    response = list_ollama_models(settings, client=client)

    assert response.state == InteractionState.PARTIAL_SUCCESS
    assert response.source == OllamaDiscoverySource.FILESYSTEM
    assert response.models[0].name == "qwen3:4b"


def test_get_ollama_status_reports_filesystem_fallback(tmp_path: Path) -> None:
    models_dir = build_fake_ollama_store(tmp_path, "qwen3:4b")
    client = FakeClient(response=None, error=ConnectionError("offline"))
    settings = OllamaDiscoverySettings(host="http://127.0.0.1:11434", models_dir=models_dir)

    status = get_ollama_status(settings, client=client)

    assert status.state == InteractionState.PARTIAL_SUCCESS
    assert status.connected is False
    assert status.source == OllamaDiscoverySource.FILESYSTEM
