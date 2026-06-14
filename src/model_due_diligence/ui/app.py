"""FastAPI application for the mdd-ui local dashboard."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from model_due_diligence import __version__
from model_due_diligence.ui.ollama_discovery import (
    OllamaDiscoverySettings,
    get_ollama_status,
    list_ollama_models,
)
from model_due_diligence.ui.scan_service import preview_scan, run_scan
from model_due_diligence.ui.schemas import (
    ErrorResponse,
    HealthResponse,
    InteractionState,
    OllamaModelsResponse,
    OllamaStatusResponse,
    ScanPreviewResponse,
    ScanResponse,
    ScanTargetRequest,
)

RunScanService = Callable[[ScanTargetRequest, Path], ScanResponse]
PreviewScanService = Callable[[ScanTargetRequest], ScanPreviewResponse]
GetOllamaStatus = Callable[[], OllamaStatusResponse]
ListOllamaModels = Callable[[], OllamaModelsResponse]


def create_app(
    *,
    discovery_settings: OllamaDiscoverySettings | None = None,
    get_status: GetOllamaStatus | None = None,
    list_models: ListOllamaModels | None = None,
    preview: PreviewScanService | None = None,
    scan: RunScanService | None = None,
) -> FastAPI:
    """Create the mdd-ui FastAPI application."""

    app = FastAPI(
        title="Model Due Diligence UI",
        description="Local static due-diligence dashboard API.",
        version=__version__,
    )
    settings = discovery_settings

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(version=__version__)

    @app.get("/api/ollama/status", response_model=OllamaStatusResponse)
    def ollama_status() -> OllamaStatusResponse:
        if get_status is not None:
            return get_status()
        return get_ollama_status(settings)

    @app.get("/api/ollama/models", response_model=OllamaModelsResponse)
    def ollama_models() -> OllamaModelsResponse:
        if list_models is not None:
            return list_models()
        return list_ollama_models(settings)

    @app.post("/api/scan/preview", response_model=ScanPreviewResponse)
    def scan_preview(request: ScanTargetRequest) -> ScanPreviewResponse:
        try:
            return (preview or preview_scan)(request)
        except (FileNotFoundError, ValueError) as exc:
            return ScanPreviewResponse(
                state=InteractionState.ERROR,
                target_type=request.target_type,
                target=request.target,
                message=str(exc),
            )

    @app.post("/api/scan", response_model=ScanResponse)
    def scan_target(request: ScanTargetRequest) -> ScanResponse:
        output_dir = Path(tempfile.mkdtemp(prefix="mdd-ui-audit-")).resolve()
        try:
            return (scan or run_scan)(request, output_dir)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(error="target_not_found", detail=str(exc)).model_dump(),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(error="invalid_target", detail=str(exc)).model_dump(),
            ) from exc

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: object, exc: HTTPException) -> JSONResponse:
        detail_obj: Any = exc.detail
        if isinstance(detail_obj, dict) and "state" in detail_obj:
            return JSONResponse(
                status_code=exc.status_code,
                content=cast(dict[str, Any], detail_obj),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error="request_failed", detail=str(exc.detail)).model_dump(),
        )

    return app
