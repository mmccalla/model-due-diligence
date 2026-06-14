# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Optional `mdd-ui` local dashboard API (`[ui]` extra) with versioned `/api/v1/` routes
- Ollama discovery with API and filesystem fallback, explicit interaction states, scan preview/run endpoints, export downloads and managed scan output retention
- Documentation: [`docs/mdd-ui.md`](docs/mdd-ui.md), wireframe component tree

### Changed

- Phase 1a hardening: versioned `/api/v1/` routes, unified error contract, `partial_success`/`warning` scan states, managed scan output retention, export downloads, health checks, structured logging

## Phase 1b.0 (in progress on `feat/mdd-ui-phase-1b-0`)

Pre-frontend cleanup milestone — see [`docs/mdd-ui-phase-1b-0.md`](docs/mdd-ui-phase-1b-0.md).

- Static asset directory scaffold at `src/model_due_diligence/ui/static/`
- Phase handoff checklist and branch map for 1b core implementers

## [0.1.0] - 2026-06-14

### Added

- Static due-diligence CLI (`mdd`) for local model files and cloned repositories
- Ollama model scanner (`mdd-ollama`) for installed models
- Native scanners: file inventory, text patterns, Python AST, binary strings, entropy, pickle heuristics, GGUF/safetensors metadata, git provenance
- External scanner adapters: ModelScan, Semgrep, Bandit, pip-audit, detect-secrets
- Risk scoring with conservative severity weights and `--fail-on` exit codes
- Markdown, JSON and SARIF report output
- Example workflow scripts and fixture-based demo paths
- CI quality gates, CodeQL analysis and PyPI release workflow

### Notes

- This is an **alpha** release. A clean report does not prove a model is safe.
- See [docs/limitations.md](docs/limitations.md) for full scope boundaries.

[0.1.0]: https://github.com/mmccalla/model-due-diligence/releases/tag/v0.1.0
