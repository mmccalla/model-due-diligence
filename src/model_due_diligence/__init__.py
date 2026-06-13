"""Static due-diligence scanner for local AI model artefacts and repositories."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("model-due-diligence")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["__version__"]
