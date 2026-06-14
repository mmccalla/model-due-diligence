"""Unit tests for the mdd-ui CLI."""

from __future__ import annotations

import builtins
import sys

from model_due_diligence.ui.cli import main, parse_args


def test_parse_args_defaults() -> None:
    args = parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8765
    assert args.reload is False


def test_main_returns_2_when_uvicorn_missing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    real_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "uvicorn":
            raise ImportError("uvicorn is not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(sys, "argv", ["mdd-ui"])

    assert main() == 2
