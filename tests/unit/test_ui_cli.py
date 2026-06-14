"""Unit tests for the mdd-ui CLI."""

from __future__ import annotations

import builtins
import logging
import sys
import types
from typing import Any

import pytest

from model_due_diligence.ui.cli import main, parse_args


def test_parse_args_defaults() -> None:
    args = parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8765
    assert args.reload is False


def test_parse_args_custom_host_port_and_reload() -> None:
    args = parse_args(["--host", "10.0.0.2", "--port", "9000", "--reload"])

    assert args.host == "10.0.0.2"
    assert args.port == 9000
    assert args.reload is True


def test_main_returns_2_when_uvicorn_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "uvicorn":
            raise ImportError("uvicorn is not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(sys, "argv", ["mdd-ui"])

    assert main() == 2


def test_main_starts_uvicorn_with_factory_and_logging(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> None:
        calls.append({"args": args, "kwargs": kwargs})

    fake_uvicorn = types.SimpleNamespace(run=fake_run)
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    with caplog.at_level(logging.INFO):
        exit_code = main(["--host", "10.0.0.1", "--port", "9999", "--reload"])

    assert exit_code == 0
    assert len(calls) == 1
    kwargs = calls[0]["kwargs"]
    assert kwargs["factory"] is True
    assert kwargs["host"] == "10.0.0.1"
    assert kwargs["port"] == 9999
    assert kwargs["reload"] is True
    assert calls[0]["args"][0] == "model_due_diligence.ui.app:create_app"
