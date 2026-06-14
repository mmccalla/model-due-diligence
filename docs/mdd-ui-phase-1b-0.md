# mdd-ui Phase 1b.0 — pre-frontend cleanup

Phase **1b.0** was the hygiene milestone between Phase **1a** (API) and Phase **1b core** (dashboard UI chrome). Phases **1a**, **1b.0**, **1b**, and **1c** are **complete on `main`** (merged via PRs #1 and #4).

## Branch map

| Branch | Scope | Status |
|--------|-------|--------|
| `feat/mdd-ui-phase-1a` | FastAPI `/api/v1/`, Ollama discovery, scan preview/run, exports | Merged → `main` |
| `feat/mdd-ui-phase-1b-0` | Docs, static scaffold, contract checks | Merged → `main` |
| `feat/mdd-ui-phase-1b` | Dashboard UI per [`ui-component-tree.md`](ui-component-tree.md) | Merged → `main` |
| `feat/mdd-ui-phase-1c` | Preview polish, a11y, export UX, stale-report UX | Merged → `main` |

## 1b.0 checklist (must pass before 1b core)

### API contract frozen

- [x] All routes under `/api/v1/` (see [`mdd-ui.md`](mdd-ui.md))
- [x] Unified `4xx` + `ErrorResponse` for preview and scan failures
- [x] `InteractionState` on success, `partial_success`, `warning`, and error paths
- [x] `scan_id` + export download route for `ExportBar`
- [x] OpenAPI route inventory test in `tests/unit/test_ui_api.py`

### Operator docs

- [x] [`mdd-ui.md`](mdd-ui.md) — install, security, endpoints, retention
- [x] [`ui-component-tree.md`](ui-component-tree.md) — component ↔ endpoint mapping
- [ ] ADR: local FastAPI dashboard vs MCP-only (optional, low priority)

### Frontend scaffold

- [x] `src/model_due_diligence/ui/static/` directory reserved for Phase 1b assets
- [x] FastAPI static mount + `index.html` shell (Phase 1b)
- [ ] CORS policy for cross-origin dev tooling (optional)

### Tests & quality

- [x] 124+ tests green; repo coverage ≥ 80%
- [x] UI package modules ≥ 76% (target 80% on `cli.py` in follow-up)
- [ ] Ollama `run_scan` integration test (deferred to Phase 2 trust hardening)

### Delivered in Phase 1b / 1c (formerly deferred)

- [x] Dark dashboard shell (`AppShell`, `HeaderBar`, `MainLayout`)
- [x] Ollama picker + path input interaction states in the browser
- [x] Risk gauge, findings table, limitations banner
- [x] Preview metadata, expandable finding evidence, export disabled until scan completes
- [x] Stale-report banner, scan elapsed timer, keyboard shortcuts (Phase 1c)

### Still deferred (post–v0.2.0)

- Async scan progress / `running` server signal (optional SSE — Phase 3)
- Rate limiting and request body size caps for non-localhost deploys (Phase 3)

## Handoff for post–1c work

1. Baseline docs and release scope: [`release-scope-v0.2.0.md`](release-scope-v0.2.0.md) (Phase 0).
2. Next milestone: ship **v0.2.0** with `[ui]` on PyPI (Phase 1 — version bump in `pyproject.toml`).
3. Read [`ui-component-tree.md`](ui-component-tree.md) and bind each component to `/api/v1/` responses — **do not infer state from missing JSON fields**; use `state` explicitly.
4. Use `GET /api/v1/scan/{scan_id}/export/{format}` for export buttons; do not guess filesystem paths client-side.
5. Run `./scripts/run-quality.sh` before each PR.

## Verification commands

```zsh
pip install -e ".[ui]"
./scripts/run-quality.sh
mdd-ui
open http://127.0.0.1:8765/docs
```
