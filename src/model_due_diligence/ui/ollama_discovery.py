"""Discover installed Ollama models via the HTTP API and local filesystem."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import httpx

from model_due_diligence.ollama import DEFAULT_OLLAMA_MODELS_DIR, MODEL_MEDIA_TYPE, OllamaModel, resolve_installed_model
from model_due_diligence.ui.schemas import (
    InteractionState,
    OllamaDiscoverySource,
    OllamaModelsResponse,
    OllamaModelSummary,
    OllamaStatusResponse,
)


class HttpClient(Protocol):
    """Minimal HTTP client surface used for Ollama discovery."""

    def get(self, url: str, *, timeout: float) -> Any:
        """Perform an HTTP GET request."""


HTTP_OK = 200
MIN_MANIFEST_PARTS = 2
REGISTRY_PREFIX_PARTS = 3
DEFAULT_OLLAMA_REGISTRY_NAME = "registry.ollama.ai"


@dataclass(frozen=True, slots=True)
class OllamaDiscoverySettings:
    """Configuration for Ollama model discovery."""

    host: str
    models_dir: Path
    timeout_seconds: float = 5.0


def default_ollama_host() -> str:
    """Return the configured Ollama host URL."""

    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def default_discovery_settings() -> OllamaDiscoverySettings:
    """Build discovery settings from environment defaults."""

    models_dir = Path(os.environ.get("OLLAMA_MODELS", str(DEFAULT_OLLAMA_MODELS_DIR))).expanduser()
    return OllamaDiscoverySettings(host=default_ollama_host(), models_dir=models_dir)


def get_ollama_status(
    settings: OllamaDiscoverySettings | None = None,
    *,
    client: HttpClient | None = None,
) -> OllamaStatusResponse:
    """Return Ollama connectivity and the active discovery source."""

    resolved = settings or default_discovery_settings()
    if _probe_ollama_api(resolved, client=client):
        return OllamaStatusResponse(
            state=InteractionState.SUCCESS,
            source=OllamaDiscoverySource.API,
            host=resolved.host,
            connected=True,
            message="Connected to Ollama server.",
        )

    if _filesystem_store_available(resolved.models_dir):
        return OllamaStatusResponse(
            state=InteractionState.PARTIAL_SUCCESS,
            source=OllamaDiscoverySource.FILESYSTEM,
            host=resolved.host,
            connected=False,
            message="Ollama server is offline. Using the local model store instead.",
        )

    return OllamaStatusResponse(
        state=InteractionState.ERROR,
        source=OllamaDiscoverySource.NONE,
        host=resolved.host,
        connected=False,
        message="Ollama server is unreachable and no local model store was found.",
    )


def list_ollama_models(
    settings: OllamaDiscoverySettings | None = None,
    *,
    client: HttpClient | None = None,
) -> OllamaModelsResponse:
    """List installed models from the Ollama API with filesystem fallback."""

    resolved = settings or default_discovery_settings()
    api_models = _list_models_from_api(resolved, client=client)
    if api_models is not None:
        if api_models:
            return OllamaModelsResponse(
                state=InteractionState.SUCCESS,
                source=OllamaDiscoverySource.API,
                host=resolved.host,
                models=api_models,
                message=f"Discovered {len(api_models)} installed model(s) from Ollama API.",
            )
        return OllamaModelsResponse(
            state=InteractionState.EMPTY,
            source=OllamaDiscoverySource.API,
            host=resolved.host,
            models=[],
            message="Ollama is running but no models are installed.",
        )

    filesystem_models = _list_models_from_filesystem(resolved.models_dir)
    if filesystem_models:
        return OllamaModelsResponse(
            state=InteractionState.PARTIAL_SUCCESS,
            source=OllamaDiscoverySource.FILESYSTEM,
            host=resolved.host,
            models=filesystem_models,
            message=(f"Ollama server is offline. Discovered {len(filesystem_models)} model(s) from the local store."),
        )

    if _filesystem_store_available(resolved.models_dir):
        return OllamaModelsResponse(
            state=InteractionState.EMPTY,
            source=OllamaDiscoverySource.FILESYSTEM,
            host=resolved.host,
            models=[],
            message="Local Ollama store found but no installed models were discovered.",
        )

    return OllamaModelsResponse(
        state=InteractionState.ERROR,
        source=OllamaDiscoverySource.NONE,
        host=resolved.host,
        models=[],
        message="Unable to discover Ollama models from the server or local store.",
    )


def _probe_ollama_api(settings: OllamaDiscoverySettings, *, client: HttpClient | None) -> bool:
    response = _fetch_tags_payload(settings, client=client)
    return response is not None


def _list_models_from_api(
    settings: OllamaDiscoverySettings,
    *,
    client: HttpClient | None,
) -> list[OllamaModelSummary] | None:
    payload = _fetch_tags_payload(settings, client=client)
    if payload is None:
        return None

    raw_models = payload.get("models")
    if not isinstance(raw_models, list):
        return []

    models: list[OllamaModelSummary] = []
    for entry in raw_models:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or entry.get("model") or "").strip()
        if not name:
            continue
        details_raw = entry.get("details")
        details: dict[str, Any] = details_raw if isinstance(details_raw, dict) else {}
        models.append(
            OllamaModelSummary(
                name=name,
                source=OllamaDiscoverySource.API,
                size_bytes=_optional_int(entry.get("size")),
                modified_at=_optional_str(entry.get("modified_at")),
                family=_optional_str(details.get("family")),
                digest=_optional_str(entry.get("digest")),
            )
        )

    return sorted(models, key=lambda model: model.name.lower())


def _fetch_tags_payload(
    settings: OllamaDiscoverySettings,
    *,
    client: HttpClient | None,
) -> dict[str, Any] | None:
    url = f"{settings.host}/api/tags"
    try:
        if client is not None:
            response = client.get(url, timeout=settings.timeout_seconds)
            if getattr(response, "status_code", HTTP_OK) != HTTP_OK:
                return None
            payload = response.json()
        else:
            with httpx.Client(timeout=settings.timeout_seconds) as httpx_client:
                http_response = httpx_client.get(url)
                if http_response.status_code != HTTP_OK:
                    return None
                payload = http_response.json()
    except Exception:
        return None

    return payload if isinstance(payload, dict) else None


def _filesystem_store_available(models_dir: Path) -> bool:
    manifests_dir = models_dir.expanduser().resolve() / "manifests"
    return manifests_dir.is_dir()


def _list_models_from_filesystem(models_dir: Path) -> list[OllamaModelSummary]:
    manifests_dir = models_dir.expanduser().resolve() / "manifests"
    if not manifests_dir.is_dir():
        return []

    discovered: dict[str, OllamaModelSummary] = {}
    for manifest_path in sorted(manifests_dir.rglob("*")):
        if not manifest_path.is_file():
            continue
        model_name = _model_name_from_manifest_path(manifests_dir, manifest_path)
        if model_name is None or model_name in discovered:
            continue
        try:
            resolved = resolve_installed_model(model_name, models_dir=models_dir)
        except (FileNotFoundError, OSError, ValueError):
            continue
        discovered[model_name] = _summary_from_resolved_model(resolved)

    return sorted(discovered.values(), key=lambda model: model.name.lower())


def _model_name_from_manifest_path(manifests_dir: Path, manifest_path: Path) -> str | None:
    relative_parts = manifest_path.relative_to(manifests_dir).parts
    if len(relative_parts) < MIN_MANIFEST_PARTS:
        return None

    tag = relative_parts[-1]
    repository_parts = relative_parts[:-1]
    if len(repository_parts) >= REGISTRY_PREFIX_PARTS and repository_parts[0] == DEFAULT_OLLAMA_REGISTRY_NAME:
        repository = "/".join(repository_parts[2:])
    else:
        repository = "/".join(repository_parts)
    if not repository:
        return None
    return f"{repository}:{tag}"


def _summary_from_resolved_model(model: OllamaModel) -> OllamaModelSummary:
    total_size = sum(layer.size for layer in model.layers)
    model_layer = next((layer for layer in model.layers if layer.media_type == MODEL_MEDIA_TYPE), None)
    return OllamaModelSummary(
        name=model.model_name,
        source=OllamaDiscoverySource.FILESYSTEM,
        size_bytes=total_size or None,
        modified_at=None,
        family=None,
        digest=model_layer.digest if model_layer is not None else None,
    )


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
