# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
