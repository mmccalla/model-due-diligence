# mdd-ui static assets (Phase 1b core)

This directory is reserved for the Phase **1b** local dashboard frontend:

- `index.html` — app shell entrypoint
- `app.css` — layout and design tokens
- `app.js` — API client and interaction-state rendering

Phase **1b.0** only establishes the directory. Do not add bundled frontend chrome until the checklist in [`docs/mdd-ui-phase-1b-0.md`](../../../../docs/mdd-ui-phase-1b-0.md) is complete.

Mount plan (Phase 1b core): serve this folder from `create_app()` via `StaticFiles` at `/` with API routes remaining under `/api/v1/`.
