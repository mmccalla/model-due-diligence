"""Lightweight contract tests for mdd-ui static assets (app.js, index.html)."""

from __future__ import annotations

import re

import pytest

from model_due_diligence.ui.app import STATIC_DIR

APP_JS = STATIC_DIR / "app.js"
INDEX_HTML = STATIC_DIR / "index.html"


@pytest.fixture
def app_js() -> str:
    return APP_JS.read_text(encoding="utf-8")


@pytest.fixture
def index_html() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def test_static_assets_exist() -> None:
    assert APP_JS.is_file()
    assert INDEX_HTML.is_file()


def test_run_scan_button_disabled_before_fetch(app_js: str) -> None:
    run_scan_start = app_js.index("async function runScan()")
    disabled_idx = app_js.index("ui.runScanButton.disabled = true", run_scan_start)
    fetch_idx = app_js.index('await apiFetch("/scan"', run_scan_start)

    assert disabled_idx < fetch_idx


def test_scan_status_shows_running_before_fetch(app_js: str) -> None:
    run_scan_start = app_js.index("async function runScan()")
    running_idx = app_js.index('setScanStatus("Running static scan…", "running")', run_scan_start)
    fetch_idx = app_js.index('await apiFetch("/scan"', run_scan_start)

    assert running_idx < fetch_idx


def test_scan_running_state_guarded(app_js: str) -> None:
    assert "scanRunning: false" in app_js
    assert "if (state.scanRunning) return;" in app_js
    assert "state.scanRunning = true" in app_js
    assert "state.scanRunning = false" in app_js


def _function_body(source: str, signature: str) -> str:
    start = source.index(signature)
    brace_start = source.index("{", start)
    depth = 0
    for index, char in enumerate(source[brace_start:], start=brace_start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace_start : index + 1]
    raise AssertionError(f"unterminated function body for {signature!r}")


def test_export_links_disabled_during_scan_and_enabled_on_complete(app_js: str) -> None:
    assert "function disableExportLinks()" in app_js
    assert "function setExportLinks(" in app_js
    assert 'setAttribute("aria-disabled", "true")' in app_js
    assert 'setAttribute("aria-disabled", "false")' in app_js

    run_scan_body = _function_body(app_js, "async function runScan()")
    disable_idx = run_scan_body.index("disableExportLinks()")
    fetch_idx = run_scan_body.index('await apiFetch("/scan"')
    assert disable_idx < fetch_idx

    render_report_body = _function_body(app_js, "function renderReport(")
    assert "setExportLinks(state.scanId)" in render_report_body


def test_scan_status_bar_has_aria_live_polite(index_html: str) -> None:
    assert 'id="scan-status-bar"' in index_html
    scan_status_region = re.search(
        r'<div[^>]*id="scan-status-bar"[^>]*>',
        index_html,
    )
    assert scan_status_region is not None
    assert 'aria-live="polite"' in scan_status_region.group(0)


def test_skip_link_and_main_landmark(index_html: str) -> None:
    assert 'class="skip-link"' in index_html
    assert 'href="#main-content"' in index_html

    main_region = re.search(r'<main[^>]*id="main-content"[^>]*>', index_html)
    assert main_region is not None
    assert 'role="main"' in main_region.group(0)


def test_export_links_aria_disabled_when_inactive(index_html: str) -> None:
    for export_id in ("export-markdown", "export-json", "export-sarif"):
        link = re.search(rf'<a[^>]*id="{export_id}"[^>]*>', index_html)
        assert link is not None, f"missing export link: {export_id}"
        assert 'aria-disabled="true"' in link.group(0)
