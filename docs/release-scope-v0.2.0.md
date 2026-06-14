# Release scope — v0.2.0

## Objective

Ship the **mdd-ui local dashboard** as an installable, documented product alongside the existing CLI. v0.2.0 is the first PyPI release that includes the `[ui]` extra and the Phase 1a–1c stack on `main`.

## In scope (delivered on `main`)

- **Packaging:** `pip install "model-due-diligence[ui]"` resolves and exposes the `mdd-ui` entry point.
- **Version:** `pyproject.toml` → `0.2.0`; `CHANGELOG.md` `[0.2.0]` section with date.
- **API:** Versioned `/api/v1/` routes — health, Ollama discovery, scan preview/run, export downloads, unified error contract and interaction states.
- **Dashboard UI:** Dark shell at `/` (`index.html`, `app.css`, `app.js`).
- **Phase 1c polish:** Preview metadata, expandable finding evidence, export disabled until scan completes, stale-report banner, scan elapsed timer, keyboard shortcuts.
- **Trust hardening (Phase 2):** Hook tests, mocked Ollama API integration test, CLI coverage.
- **UI polish (Phase 3):** Export disable on scan start; static contract and a11y tests.
- **Security docs (Phase 5):** `SECURITY.md` localhost/PII guidance.
- **Operator docs:** [`mdd-ui.md`](mdd-ui.md), [`ui-component-tree.md`](ui-component-tree.md), phase handoff docs synced.
- **First-run story:** README quick start covers both `mdd` and `mdd-ui`.

## Out of scope (future work)

- **SSE / server scan progress:** Backend status endpoint or SSE (client running state only today).
- **Non-localhost hardening:** Rate limiting, request body size caps, auth/TLS beyond localhost warnings.
- **Scanner roadmap (Phase 4):** GGUF/safetensors depth, Hugging Face metadata, SBOM, Sigstore/SLSA, licence rules, behavioural harness.
- **Optional hygiene:** ADR (FastAPI vs MCP-only), CORS for cross-origin dev tooling.
- **Live Ollama in default CI:** Optional `@pytest.mark.ollama` test only.

## Exit criteria for v0.2.0 tag

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Phase 0 baseline docs merged | Done (#5) |
| 2 | `pyproject.toml` `0.2.0`; CHANGELOG `[0.2.0]` dated | Done (#10) |
| 3 | `./scripts/run-quality.sh` green on `main` | Done (158 tests, ~83% coverage) |
| 4 | `pip install -e ".[ui]"` + `mdd-ui` serves `/` and `/api/v1/health` | Done (local verify) |
| 5 | Tag `v0.2.0` → GitHub release + PyPI publish | Done ([release run](https://github.com/mmccalla/model-due-diligence/actions/runs/27513017317)) |
| 6 | README install/first-run for CLI and dashboard | Done |

**Does not require:** SSE backend, scanner roadmap, full WCAG audit, or beta classifier bump.

## After v0.2.0

See README [Roadmap](../README.md#roadmap) for scanner depth (Phase 4 track) and optional UI hardening (SSE, rate limits).
