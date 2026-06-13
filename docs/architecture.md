# Architecture

## Purpose

`model-due-diligence` is a Python command-line tool for performing static supply-chain due diligence on local AI model files and cloned model repositories before they are imported into local runtimes such as Ollama, llama.cpp, LM Studio or Transformers.

The tool is designed to reduce practical risk from unsafe serialisation, suspicious repository content, weak provenance, exposed secrets, unexpected binaries, unsafe dependency files and malformed model metadata.

It does **not** prove that model weights are safe. It is a risk-reduction gate, not a mathematical guarantee.

## Architectural Style

The project uses a **modular monolith** architecture:

```text
CLI -> App -> Inventory -> Native Scanners -> External Scanner Adapters -> Risk Scorer -> Reports
```

This keeps deployment simple while preserving clear internal boundaries. The package should remain a single Python CLI until there is a genuine operational reason to split it.

## Runtime Flow

```text
User runs CLI
  |
  v
Parse command-line options
  |
  v
Build scan context
  |
  v
Create file inventory
  |
  v
Run native scanners
  |
  v
Run optional external scanners
  |
  v
Score findings
  |
  v
Write Markdown / JSON / optional SARIF reports
  |
  v
Return process exit code based on --fail-on threshold
```

## Core Components

| Component | Responsibility | Should Not Do |
|---|---|---|
| `cli.py` | Parse arguments, validate user input, return process exit code | Perform scanning logic |
| `app.py` | Orchestrate the scan lifecycle | Contain scanner-specific rules |
| `domain/` | Define `Finding`, `Severity`, `RiskLevel`, reports and shared models | Call external tools |
| `inventory/` | List files, calculate hashes, inspect permissions and symlinks | Score risk |
| `scanners/` | Perform native static checks without external tools | Write reports directly |
| `external/` | Wrap tools such as ModelScan, Semgrep, Bandit, pip-audit, detect-secrets, Ruff, Pyright and mypy | Interpret findings outside the common domain model |
| `reporting/` | Render Markdown, JSON and optional SARIF outputs | Run scanners |
| `config/` | Hold defaults, extension lists and suspicious pattern definitions | Contain orchestration logic |
| `tests/` | Validate scanner behaviour, risk scoring, CLI smoke tests and report generation | Depend on live external services |

## Internal Dependency Direction

Dependencies should flow in one direction:

```text
cli -> app -> domain
app -> inventory
app -> scanners
app -> external
app -> reporting
scanners -> domain/config
external -> domain/config/command_runner
reporting -> domain
```

Avoid reverse dependencies. In particular:

- scanners must not import `app`;
- reporters must not run scanners;
- external scanner adapters must not write the final report;
- domain models must not depend on infrastructure modules.

## Scanner Model

All scanners should return normalised findings using the shared domain model.

```text
Native scanner result  -> Finding[]
External scanner result -> ToolResult + Finding[]
Inventory result -> FileRecord[] + Finding[]
```

This allows the risk scorer and reporters to work consistently regardless of whether the evidence came from native code or a third-party scanner.

## Native Scanner Responsibilities

Native scanners provide deterministic static checks that do not execute the model or repository code.

| Scanner | Purpose |
|---|---|
| File inventory | Hashes, file types, symlinks, executable permissions and unusual artefacts |
| Text pattern scanner | Suspicious shell, network, secret, environment and obfuscation patterns |
| Python AST scanner | Dangerous Python calls such as `eval`, `exec`, `pickle.load`, `os.system` and `subprocess` |
| Binary string scanner | URLs, shell paths, tokens, destructive commands and network indicators in binary files |
| Entropy scanner | High-entropy non-model artefacts that may indicate packed, encrypted or unusual content |
| Model metadata scanner | GGUF magic/version checks and safetensors header inspection |
| Pickle heuristic scanner | Extra indicators of risky pickle-like payloads in high-risk serialisation formats |
| Git provenance scanner | Remote URL, commit hash, dirty tree and Git LFS metadata |

Native scanners should be conservative: findings are prompts for review, not proof of compromise.

## External Scanner Responsibilities

External scanner adapters run established security tools and capture their outputs as evidence.

| Tool | Role |
|---|---|
| ModelScan | Static model serialisation scanning |
| Semgrep | Static application security scanning across code/config |
| Bandit | Python security linting |
| pip-audit | Python dependency vulnerability scanning |
| detect-secrets | Secret detection |
| Ruff | Linting and format checks for this project |
| Pyright | Static type checking |
| mypy | Static type checking |
| CodeQL | Repository-level semantic security analysis via GitHub Actions |

External scanner adapters should be thin wrappers around command execution. They should not own policy decisions beyond mapping tool availability or non-zero exits into normalised findings.

## Risk Scoring

The risk scorer converts findings and scanner tool outcomes into a bounded score and risk level.

Suggested interpretation:

| Risk Level | Meaning | Action |
|---|---|---|
| LOW | No obvious static artefact risks found | Acceptable for sandboxed first run |
| MEDIUM | Review required | Do not import until findings are understood |
| HIGH | Material risk indicators present | Do not load unless every finding is justified |
| CRITICAL | Severe or multiple high-risk indicators | Treat as unsafe by default |

The score is intentionally conservative. It should be used as a decision aid, not as an automated trust decision.

## Reporting

Reports should be reproducible and reviewable.

Required outputs:

```text
model_due_diligence_report.md
model_due_diligence_report.json
```

Optional output:

```text
model_due_diligence_report.sarif
```

The Markdown report is for humans. The JSON report is for automation and regression testing. SARIF is useful for GitHub code scanning integration.

Reports should include:

- scanned path;
- timestamp;
- risk level and score;
- summary counts;
- findings with severity, category, evidence and recommendation;
- model metadata;
- external scanner results;
- file inventory with SHA-256 hashes;
- explicit limitations.

## GitHub Automation

The repository automation is intentionally aligned with the security purpose of the tool.

| File | Purpose |
|---|---|
| `.github/workflows/ci.yml` | Ruff, Pyright, mypy, pytest and CLI smoke test |
| `.github/workflows/codeql.yml` | Weekly and event-driven CodeQL analysis using extended security queries |
| `.github/workflows/release.yml` | Build, validate, upload artefacts, create GitHub release and publish to PyPI on version tags |
| `.github/dependabot.yml` | Weekly dependency and GitHub Actions update checks with grouped minor/patch updates |
| `.github/pull_request_template.md` | Change classification, quality gates, supply-chain review and release impact checks |

## Security Boundaries

The tool should not:

- load or execute model weights;
- execute repository scripts as part of normal scanning;
- require network access during a local scan;
- read user secrets beyond detecting whether secrets have accidentally been committed;
- send scan artefacts to external services;
- treat a clean scan as proof of safety.

The recommended operating model is:

```text
Official or reputable source
+ pinned commit or hash
+ static due-diligence scan
+ first run in a no-network sandbox
+ no credentials mounted
+ adversarial behavioural test suite
= reasonable practical risk reduction
```

## Design Principles

1. **No model execution during scanning**  
   Scanning must be static by default.

2. **Simple deployment**  
   Keep the project as a single Python package and CLI.

3. **Clear module boundaries**  
   Scanner logic, orchestration, reporting and risk scoring must stay separate.

4. **Reviewable evidence**  
   Every material finding should have a category, severity, evidence and recommendation.

5. **Fail safely**  
   Missing scanners, unreadable files and malformed metadata should be visible in the report.

6. **Low false certainty**  
   Reports must state that weight-level poisoning and subtle behavioural backdoors are not reliably detectable through static scanning.

7. **CI from day one**  
   Quality, type checking, tests, CodeQL and dependency updates are part of the architecture, not afterthoughts.

## Extension Points

Future scanners should follow the existing pattern:

```text
new scanner -> returns Finding[] or ToolResult + Finding[] -> app orchestrates -> risk scorer evaluates -> reporters render
```

Potential future extensions:

- SBOM generation;
- Sigstore or SLSA provenance checks;
- Hugging Face metadata retrieval using pinned revisions;
- model-card quality scoring;
- licence compatibility checks;
- SARIF upload in CI;
- adversarial behavioural test harness for local sandboxed inference.

## Known Limitations

This architecture does not reliably detect:

- malicious behaviour encoded directly into model weights;
- sleeper-agent or trigger-based model backdoors;
- training-data poisoning;
- all pickle deserialisation evasions;
- malicious behaviour that only appears after fine-tuning;
- prompt-injection obedience in downstream RAG workflows.

Those risks require additional controls: provenance verification, sandboxing, behavioural tests, runtime isolation, restricted credentials and human review.