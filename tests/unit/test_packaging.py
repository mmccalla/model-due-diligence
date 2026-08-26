"""Packaging and release metadata smoke tests."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from model_due_diligence.ui.app import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def _load_pyproject() -> dict[str, object]:
    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


def _project_version() -> str:
    data = _load_pyproject()
    project = data.get("project")
    assert isinstance(project, dict)
    version = project.get("version")
    assert isinstance(version, str)
    return version


def _ui_optional_dependencies() -> list[str]:
    data = _load_pyproject()
    project = data.get("project")
    assert isinstance(project, dict)
    optional = project.get("optional-dependencies")
    assert isinstance(optional, dict)
    ui_deps = optional.get("ui")
    assert isinstance(ui_deps, list)
    return [str(dep) for dep in ui_deps]


def test_pyproject_version_is_valid_semver() -> None:
    version = _project_version()

    assert SEMVER_PATTERN.fullmatch(version) is not None
    assert version == "0.2.0"


def test_mypy_skips_numpy_stub_imports() -> None:
    data = _load_pyproject()
    tool = data.get("tool")
    assert isinstance(tool, dict)
    mypy = tool.get("mypy")
    assert isinstance(mypy, dict)
    overrides = mypy.get("overrides")
    assert isinstance(overrides, list)

    numpy_override = next(
        (
            item
            for item in overrides
            if isinstance(item, dict) and "numpy" in {str(module) for module in item.get("module") or []}
        ),
        None,
    )

    assert numpy_override is not None
    assert numpy_override.get("follow_imports") == "skip"


def test_ui_optional_dependency_includes_fastapi_and_uvicorn() -> None:
    ui_deps = _ui_optional_dependencies()
    joined = " ".join(ui_deps).lower()

    assert "fastapi" in joined
    assert "uvicorn" in joined


def test_create_app_import_works() -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("uvicorn")

    assert callable(create_app)
