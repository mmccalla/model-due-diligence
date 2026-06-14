"""Health checks for the mdd-ui API."""

from __future__ import annotations

from typing import Literal

from model_due_diligence.app import ModelDueDiligenceApp

ScannerEngineStatus = Literal["ready", "unavailable"]
HealthStatus = Literal["ok", "degraded"]


def scanner_engine_status() -> ScannerEngineStatus:
    """Return whether the core scan engine can be initialised."""

    try:
        _ = ModelDueDiligenceApp
    except Exception:
        return "unavailable"
    return "ready"


def health_status() -> HealthStatus:
    """Return aggregate API health based on scanner engine readiness."""

    return "ok" if scanner_engine_status() == "ready" else "degraded"
