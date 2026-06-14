"""FastAPI application for the mdd-ui local dashboard."""

# pyright: reportUnusedFunction=false

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from model_due_diligence import __version__
from model_due_diligence.ui.health import health_status, scanner_engine_status
from model_due_diligence.ui.ollama_discovery import (
    OllamaDiscoverySettings,
    get_ollama_status,
    list_ollama_models,
)
from model_due_diligence.ui.output_manager import ScanOutputManager, default_output_manager
from model_due_diligence.ui.scan_service import preview_scan, run_scan
from model_due_diligence.ui.schemas import (
    ErrorResponse,
    HealthResponse,
    OllamaModelsResponse,
    OllamaStatusResponse,
    ScanPreviewResponse,
    ScanResponse,
    ScanTargetRequest,
)

API_V1_PREFIX = "/api/v1"

RunScanService = Callable[[ScanTargetRequest, Path, str], ScanResponse]
PreviewScanService = Callable[[ScanTargetRequest], ScanPreviewResponse]
GetOllamaStatus = Callable[[], OllamaStatusResponse]
ListOllamaModels = Callable[[], OllamaModelsResponse]

logger = logging.getLogger(__name__)


def _scan_error_response(error: str, detail: str, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(error=error, detail=detail).model_dump(),
    )


def create_app(
    *,
    discovery_settings: OllamaDiscoverySettings | None = None,
    output_manager: ScanOutputManager | None = None,
    get_status: GetOllamaStatus | None = None,
    list_models: ListOllamaModels | None = None,
    preview: PreviewScanService | None = None,
    scan: RunScanService | None = None,
) -> FastAPI:
    """Create the mdd-ui FastAPI application."""

    manager = output_manager or default_output_manager()
    settings = discovery_settings

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        manager.cleanup_stale()
        logger.info("mdd-ui API started version=%s output_root=%s", __version__, manager.root)
        yield

    app = FastAPI(
        title="Model Due Diligence UI",
        description="Local static due-diligence dashboard API.",
        version=__version__,
        lifespan=lifespan,
    )

    @app.get(f"{API_V1_PREFIX}/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        engine = scanner_engine_status()
        return HealthResponse(
            version=__version__,
            status=health_status(),
            scanner_engine=engine,
        )

    @app.get(f"{API_V1_PREFIX}/ollama/status", response_model=OllamaStatusResponse)
    def ollama_status() -> OllamaStatusResponse:
        if get_status is not None:
            return get_status()
        return get_ollama_status(settings)

    @app.get(f"{API_V1_PREFIX}/ollama/models", response_model=OllamaModelsResponse)
    def ollama_models() -> OllamaModelsResponse:
        if list_models is not None:
            return list_models()
        return list_ollama_models(settings)

    @app.post(f"{API_V1_PREFIX}/scan/preview", response_model=ScanPreviewResponse)
    def scan_preview(request: ScanTargetRequest) -> ScanPreviewResponse:
        try:
            return (preview or preview_scan)(request)
        except FileNotFoundError as exc:
            raise _scan_error_response("target_not_found", str(exc), 404) from exc
        except ValueError as exc:
            raise _scan_error_response("invalid_target", str(exc), 400) from exc

    @app.post(f"{API_V1_PREFIX}/scan", response_model=ScanResponse)
    def scan_target(request: ScanTargetRequest) -> ScanResponse:
        scan_id, output_dir = manager.create_output_dir()
        try:
            return (scan or run_scan)(request, output_dir, scan_id)
        except FileNotFoundError as exc:
            raise _scan_error_response("target_not_found", str(exc), 404) from exc
        except ValueError as exc:
            raise _scan_error_response("invalid_target", str(exc), 400) from exc

    @app.get(f"{API_V1_PREFIX}/scan/{{scan_id}}/export/{{report_format}}")
    def export_scan(scan_id: str, report_format: str) -> FileResponse:
        try:
            export_path = manager.resolve_export_path(scan_id, report_format)
        except ValueError as exc:
            raise _scan_error_response("invalid_export_request", str(exc), 400) from exc
        except FileNotFoundError as exc:
            raise _scan_error_response("export_not_found", str(exc), 404) from exc

        media_types = {
            "markdown": "text/markdown",
            "json": "application/json",
            "sarif": "application/sarif+json",
        }
        return FileResponse(
            path=export_path,
            media_type=media_types.get(report_format, "application/octet-stream"),
            filename=export_path.name,
        )

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
