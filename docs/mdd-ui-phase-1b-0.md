# mdd-ui Phase 1b.0 — pre-frontend cleanup

Phase **1b.0** was the hygiene milestone between Phase **1a** (API) and Phase **1b core** (dashboard UI chrome). Phases **1a**, **1b.0**, **1b**, and **1c** are **complete on `main`**. Follow-on polish phases **2**, **3**, and **5** (trust tests, UI polish, security docs) are also merged.

## Branch map (historical)

| Branch | Scope | Status |
|--------|-------|--------|
| `feat/mdd-ui-phase-1a` | FastAPI `/api/v1/`, Ollama discovery, scan preview/run, exports | Merged → `main` |
| `feat/mdd-ui-phase-1b-0` | Docs, static scaffold, contract checks | Merged → `main` |
| `feat/mdd-ui-phase-1b` | Dashboard UI per [`ui-component-tree.md`](ui-component-tree.md) | Merged → `main` |
| `feat/mdd-ui-phase-1c` | Preview polish, a11y, export UX, stale-report UX | Merged → `main` |

## 1b.0 checklist (complete)

### API contract frozen

- [x] All routes under `/api/v1/` (see [`mdd-ui.md`](mdd-ui.md))
- [x] Unified `4xx` + `ErrorResponse` for preview and scan failures
- [x] `InteractionState` on success, `partial_success`, `warning`, and error paths
- [x] `scan_id` + export download route for `ExportBar`
- [x] OpenAPI route inventory test in `tests/unit/test_ui_api.py`

### Operator docs

- [x] [`mdd-ui.md`](mdd-ui.md) — install, security, endpoints, retention
- [x] [`ui-component-tree.md`](ui-component-tree.md) — component ↔ endpoint mapping

### Frontend scaffold

- [x] `src/model_due_diligence/ui/static/` directory reserved for Phase 1b assets
- [x] FastAPI static mount + `index.html` shell (Phase 1b)

### Tests & quality

- [x] 158+ tests green; repo coverage ≥ 80%
- [x] UI `cli.py` covered (Phase 2 trust hardening)
- [x] Mocked Ollama scan via UI API (`tests/integration/test_ui_ollama_scan.py`, Phase 2)
- [x] Git hook regression tests (`tests/unit/test_git_hooks.py`, Phase 2)

### Delivered in Phase 1b / 1c

- [x] Dark dashboard shell (`AppShell`, `HeaderBar`, `MainLayout`)
- [x] Ollama picker + path input interaction states in the browser
- [x] Risk gauge, findings table, limitations banner
- [x] Preview metadata, expandable finding evidence, export disabled until scan completes
- [x] Stale-report banner, scan elapsed timer, keyboard shortcuts (Phase 1c)

### Delivered in Phase 3 (UI polish)

- [x] Export links disabled at scan start (client-side running state)
- [x] Static contract + a11y landmark tests (`tests/unit/test_ui_static_contract.py`)

## Optional / future (not required for v0.2.0)

- ADR: local FastAPI dashboard vs MCP-only
- CORS policy for cross-origin dev tooling
- Server-side SSE or polling status endpoint for long-running scans
- Rate limiting and request body size caps for non-localhost deploys
- Live Ollama integration test in CI (`@pytest.mark.ollama`, skipped by default)

## Verification commands

```zsh
pip install -e ".[ui]"
./scripts/run-quality.sh
mdd-ui
open http://127.0.0.1:8765/
```
