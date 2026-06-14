# mdd-ui Phase 1b.0 — pre-frontend cleanup

Phase **1b.0** is a short hygiene milestone between the Phase **1a** API (merged or on `feat/mdd-ui-phase-1a`) and Phase **1b core** (dashboard UI chrome). It exists so frontend work starts from a stable, documented contract — not from leftover API gaps.

## Branch map

| Branch | Scope | Status |
|--------|-------|--------|
| `feat/mdd-ui-phase-1a` | FastAPI `/api/v1/`, Ollama discovery, scan preview/run, exports | Ready for PR → `main` |
| `feat/mdd-ui-phase-1b-0` | Docs, static scaffold, contract checks (this milestone) | In progress |
| `feat/mdd-ui-phase-1b` | Dashboard UI per [`ui-component-tree.md`](ui-component-tree.md) | Not started |

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
- [ ] FastAPI static mount + `index.html` shell (Phase 1b core)
- [ ] CORS policy for same-origin static serving (Phase 1b core)

### Tests & quality

- [x] 124 tests green; repo coverage ≥ 80%
- [x] UI package modules ≥ 76% (target 80% on `cli.py` in 1b core)
- [ ] Ollama `run_scan` integration test (deferred to 1b.0 follow-up or 1b core)

### Deferred to Phase 1b core (not 1b.0)

- Dark dashboard shell (`AppShell`, `HeaderBar`, `MainLayout`)
- Ollama picker + path input interaction states in the browser
- Risk gauge, findings table, limitations banner
- Async scan progress / `running` server signal (optional SSE)
- Rate limiting and request body size caps for non-localhost deploys

## Handoff for 1b core implementers

1. Merge or rebase onto `feat/mdd-ui-phase-1a` (or `main` once PR lands).
2. Read [`ui-component-tree.md`](ui-component-tree.md) and bind each component to `/api/v1/` responses — **do not infer state from missing JSON fields**; use `state` explicitly.
3. Place static assets under `src/model_due_diligence/ui/static/` and mount from `create_app()` when adding the HTML shell.
4. Use `GET /api/v1/scan/{scan_id}/export/{format}` for export buttons; do not guess filesystem paths client-side.
5. Run `./scripts/run-quality.sh` before each PR.

## Verification commands

```zsh
pip install -e ".[ui]"
./scripts/run-quality.sh
mdd-ui
open http://127.0.0.1:8765/docs
```
