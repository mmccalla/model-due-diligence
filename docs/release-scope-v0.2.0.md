# Release scope — v0.2.0

## Objective

Ship the **mdd-ui local dashboard** as an installable, documented product alongside the existing CLI. v0.2.0 is the first PyPI release that includes the `[ui]` extra and the Phase 1a–1c stack merged on `main`.

## In scope (mdd-ui stack)

- **Packaging:** `pip install "model-due-diligence[ui]"` resolves and exposes the `mdd-ui` entry point.
- **Version bump:** `pyproject.toml` → `0.2.0` and aligned `CHANGELOG.md` section (Phase 1 — not this doc PR).
- **API:** Versioned `/api/v1/` routes — health, Ollama discovery, scan preview/run, export downloads, unified error contract and interaction states.
- **Dashboard UI:** Dark shell at `/` implementing the wireframe component tree (`index.html`, `app.css`, `app.js`).
- **Phase 1c polish:** Preview metadata, expandable finding evidence, export disabled until scan completes, stale-report banner, scan elapsed timer, keyboard shortcuts.
- **Operator docs:** [`mdd-ui.md`](mdd-ui.md), [`ui-component-tree.md`](ui-component-tree.md), phase handoff docs synced to merged state.
- **Release automation:** Tag `v0.2.0`, GitHub release notes, PyPI publish via existing release workflow.
- **First-run story:** README quick start covers both `mdd` and `mdd-ui` with a minimal example path.

## Out of scope (deferred)

- **SSE / live scan progress:** Server-sent events or polling status endpoint for long-running scans (Phase 3).
- **Non-localhost hardening:** Rate limiting, request body size caps, authentication/TLS guidance beyond localhost warnings.
- **Scanner roadmap:** GGUF/safetensors depth, Hugging Face metadata, SBOM, Sigstore/SLSA, licence rules, behavioural harness (Phase 4 track).
- **Optional hygiene:** ADR (FastAPI vs MCP-only), CORS for cross-origin dev tooling.
- **Ollama integration test in default CI:** Live or fully mocked end-to-end Ollama scan via UI API (Phase 2).

## Exit criteria for v0.2.0 tag

All of the following must pass before tagging:

1. Phase 0 baseline docs merged — phase status and this release scope document reflect `main`.
2. `pyproject.toml` version is `0.2.0`; `[Unreleased]` in `CHANGELOG.md` moved to `[0.2.0]` with date.
3. `./scripts/run-quality.sh` green on the release commit.
4. `pip install -e ".[ui]"` and `mdd-ui` serves dashboard at `/` and `/api/v1/health` returns readiness.
5. GitHub release workflow publishes wheel/sdist to PyPI with `[ui]` optional dependency documented.
6. README documents install and first run for both CLI and dashboard.

**Does not require:** SSE, scanner roadmap items, WCAG audit, or beta classifier bump.
