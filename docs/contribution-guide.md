# Contributing

Run Ruff, Pyright, mypy and pytest before submitting changes.

# Contribution Guide

## Purpose

Thank you for contributing to `model-due-diligence`.

This project is a security-oriented Python CLI for performing static due-diligence checks on local AI model files and cloned model repositories. Contributions should therefore prioritise correctness, maintainability, clear evidence, conservative risk handling and explicit limitations.

A clean scan must never be presented as proof that a model is safe. The tool reduces practical supply-chain risk; it does not prove the absence of malicious weights, sleeper-agent behaviour, prompt-injection risk or all unsafe deserialisation techniques.

## Development Principles

Follow these principles for all changes:

1. **Do not execute model artefacts during scanning**  
   Scanners must remain static by default.

2. **Keep the modular monolith simple**  
   Add clear modules and tests; do not introduce distributed services, background workers or unnecessary abstraction.

3. **Return normalised findings**  
   Native scanners should return `Finding[]`. External scanner adapters should return `ToolResult` plus any normalised `Finding[]`.

4. **Keep responsibilities separated**  
   CLI parses options. `app.py` orchestrates. Scanners scan. Risk scoring scores. Reporters render.

5. **Fail visibly and safely**  
   Missing tools, unreadable files, malformed metadata and unsupported formats should appear in reports.

6. **Avoid false certainty**  
   New checks should describe false-positive and false-negative risks where relevant.

## Repository Layout

```text
src/model_due_diligence/
├── cli.py                  # command-line interface
├── app.py                  # scan orchestration
├── domain/                 # shared models and risk concepts
├── inventory/              # file discovery, hashes, symlinks and permissions
├── scanners/               # native static scanners
├── external/               # external tool adapters
├── reporting/              # Markdown, JSON and optional SARIF reports
└── config/                 # defaults and scanner patterns

tests/
├── unit/
├── integration/
└── fixtures/

docs/
.github/
```

Keep new functionality in the closest existing module before creating a new package.

## Local Setup

Create and activate a virtual environment:

```zsh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the package with development and scanner dependencies:

```zsh
python -m pip install -e ".[dev,scanners]"
```

Verify the CLI is available:

```zsh
mdd --help
model-due-diligence --help
```

## Required Quality Gates

Run these before opening a pull request:

```zsh
ruff format --check src tests
ruff check src tests
pyright
mypy src tests
pytest
mdd tests/fixtures/safe_repo --out ./audit-smoke --fail-on critical --skip-external
```

Use `--skip-external` for the smoke test because CI should remain stable and should not depend on all optional scanner tools being available or fast.

## Optional Full Local Scan

For a more complete local validation run:

```zsh
mdd tests/fixtures/suspicious_repo \
  --out ./audit-suspicious \
  --fail-on critical
```

Review the generated reports:

```text
audit-suspicious/model_due_diligence_report.md
audit-suspicious/model_due_diligence_report.json
```

## Adding a Native Scanner

Native scanners must not execute repository code, model weights or model loading paths.

When adding a scanner:

1. Add the scanner under `src/model_due_diligence/scanners/`.
2. Return normalised `Finding` objects.
3. Add configuration constants under `config/` if the scanner needs shared patterns or extension lists.
4. Add unit tests under `tests/unit/`.
5. Add at least one fixture if the scanner needs representative files.
6. Update `docs/scanner-coverage.md` and `docs/limitations.md` if coverage or limitations change.

A scanner should generally follow this shape:

```python
from pathlib import Path

from model_due_diligence.domain.models import Finding


class ExampleScanner:
    def scan(self, target: Path) -> list[Finding]:
        findings: list[Finding] = []
        # Static inspection only.
        return findings
```

## Adding an External Scanner Adapter

External scanner adapters should be thin wrappers around command execution.

When adding an adapter:

1. Add the adapter under `src/model_due_diligence/external/`.
2. Use the shared command runner.
3. Do not let the adapter write final project reports directly.
4. Capture stdout, stderr, exit code and generated artefact paths.
5. Convert only high-level tool availability or execution problems into normalised findings.
6. Keep tool-specific raw output in the output directory for review.
7. Add tests that mock command execution rather than requiring the external binary.

## Risk Scoring Changes

Risk scoring changes require extra care because they affect automated decisions.

Any pull request that changes risk scoring must include:

- the rationale for the scoring change;
- before/after examples;
- test coverage for affected severities;
- notes on false positives and false negatives;
- updates to `docs/architecture.md` or `docs/scanner-coverage.md` if interpretation changes.

The score should remain conservative and bounded. It is a decision aid, not an automated trust verdict.

## Reporting Changes

Reports are part of the product interface.

Changes to Markdown, JSON or SARIF output should include:

- tests for report generation;
- stable field names where possible;
- backwards-compatible JSON changes unless a breaking change is intentional;
- sample output in `examples/` where useful;
- clear evidence and recommendations for material findings.

## Dependency Changes

This is a supply-chain-focused project, so dependencies should be added sparingly.

Before adding a dependency, check:

- whether the standard library is sufficient;
- whether the dependency is actively maintained;
- whether the licence is compatible;
- whether the dependency is runtime, scanner-only or development-only;
- whether it materially increases install time or CI instability.

Add dependencies to the correct section in `pyproject.toml`:

- runtime dependencies under `[project].dependencies`;
- optional scanner integrations under `[project.optional-dependencies].scanners`;
- development tools under `[project.optional-dependencies].dev`.

## Security and Supply-Chain Rules

Do not commit:

- secrets, tokens, credentials or private keys;
- client data;
- large model artefacts;
- downloaded third-party model weights;
- unexplained binaries;
- generated audit reports that contain sensitive local paths or evidence.

If a fixture needs suspicious content, keep it synthetic and harmless.

## Pull Request Checklist

Before submitting, confirm:

- [ ] The change is scoped and described clearly.
- [ ] `ruff format --check src tests` passes.
- [ ] `ruff check src tests` passes.
- [ ] `pyright` passes.
- [ ] `mypy src tests` passes.
- [ ] `pytest` passes.
- [ ] CLI smoke test passes.
- [ ] New scanner behaviour has unit tests.
- [ ] New dependencies are justified.
- [ ] Security limitations are documented where relevant.
- [ ] README or docs are updated where behaviour changes.

## Release Notes

User-visible changes should include release-note wording in the pull request. Security-relevant changes should state whether they affect:

- scanner coverage;
- risk scoring;
- report format;
- CLI flags;
- external scanner behaviour;
- dependency or packaging behaviour.

## Code Style

Use clear, explicit Python.

Prefer:

- small functions;
- typed dataclasses or Pydantic-style models only where justified;
- deterministic outputs;
- dependency injection for external command runners in tests;
- conservative error handling.

Avoid:

- hidden network calls;
- implicit model loading;
- global mutable state;
- broad exception swallowing without findings or logs;
- clever abstractions that obscure scanner behaviour.

## Limitations to Preserve

Documentation and report text must continue to state that static scanning cannot reliably detect:

- malicious behaviour encoded directly in model weights;
- sleeper-agent or trigger-based backdoors;
- training-data poisoning;
- all unsafe deserialisation evasions;
- prompt-injection obedience in downstream RAG workflows;
- malicious behaviour that appears only after fine-tuning or tool integration.

These limitations are part of the project’s trust model and must not be softened.