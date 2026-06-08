# Scanner Coverage

## Purpose

This document describes the current scanner coverage for `model-due-diligence`.

The tool performs static supply-chain due diligence on local AI model files and cloned model repositories. It combines native deterministic checks with optional external scanner integrations and produces normalised findings, risk scores and reviewable reports.

Coverage is intentionally conservative. A finding is evidence for review, not proof of compromise. Absence of findings is not proof of safety.

## Coverage Summary

| Coverage Area | Native Support | External Support | Status |
|---|---:|---:|---|
| File inventory, hashes and permissions | Yes | No | Covered |
| Symlink detection | Yes | No | Covered |
| Executable/script detection | Yes | Semgrep / Bandit | Covered |
| High-risk serialisation format detection | Yes | ModelScan | Covered |
| Pickle heuristic indicators | Yes | ModelScan | Covered |
| GGUF header inspection | Yes | No | Basic coverage |
| Safetensors header inspection | Yes | No | Basic coverage |
| Suspicious text/code patterns | Yes | Semgrep / Bandit | Covered |
| Python AST dangerous-call detection | Yes | Bandit / CodeQL | Covered |
| Binary string indicators | Yes | No | Basic coverage |
| High-entropy anomaly detection | Yes | No | Basic coverage |
| Secrets detection | Yes | detect-secrets | Covered |
| Dependency vulnerability checks | No | pip-audit / Dependabot | Covered for Python dependency files |
| Git provenance checks | Yes | No | Basic coverage |
| Project code quality | No | Ruff / Pyright / mypy / pytest | Covered |
| Repository semantic security analysis | No | CodeQL | Covered in GitHub Actions |
| SARIF upload | Planned | CodeQL native SARIF | Partial |
| SBOM generation | No | No | Planned |
| Sigstore / SLSA provenance | No | No | Planned |
| Licence compatibility checks | No | No | Planned |
| Model-card quality checks | No | No | Planned |
| Weight-level backdoor detection | No | No | Not reliably detectable |
| Runtime behavioural testing | No | No | Planned separately |

## Native Scanners

Native scanners run locally without executing repository code or loading model weights.

### File Inventory Scanner

**Purpose:** create a reproducible inventory of scanned artefacts.

Checks include:

- file path;
- file extension;
- file size;
- SHA-256 hash;
- file category;
- symlink status and target;
- executable permission bits;
- basic artefact classification.

Typical findings:

- symlink detected;
- compiled binary detected;
- script or executable detected;
- executable permission bit set;
- high-risk serialisation format detected;
- lower-risk model format detected.

### Suspicious Text Pattern Scanner

**Purpose:** detect suspicious strings in text-like files.

Checks include patterns for:

- shell execution;
- network access;
- destructive file operations;
- secrets and credential terms;
- obfuscation;
- environment-variable access;
- reverse-shell indicators;
- package installation commands;
- `trust_remote_code=True`.

Typical findings:

- `suspicious_text:shell_execution`;
- `suspicious_text:network_access`;
- `suspicious_text:secret_terms`;
- `suspicious_text:transformers_remote_code`.

### Python AST Scanner

**Purpose:** inspect Python code structurally rather than only by string matching.

Checks include dangerous calls such as:

- `eval`;
- `exec`;
- `pickle.load`;
- `pickle.loads`;
- `marshal.loads`;
- `os.system`;
- `subprocess.run`;
- `subprocess.Popen`;
- `subprocess.call`;
- `subprocess.check_call`;
- `subprocess.check_output`.

Typical findings:

- dangerous Python call detected;
- Python syntax error that may prevent complete static analysis.

### Binary String Scanner

**Purpose:** extract ASCII strings from non-text files and look for suspicious indicators.

Checks include:

- URLs;
- shell paths;
- Windows shell indicators;
- environment-variable names;
- destructive command strings.

This is a heuristic scanner. Binary strings are not proof of compromise and require manual review.

### Entropy Scanner

**Purpose:** identify high-entropy non-model files that may be packed, encrypted, compressed or unusual.

Checks include:

- high entropy in files that are not expected model artefacts;
- unusual binary-like files in model repositories.

This scanner intentionally excludes normal model file extensions from entropy scoring because model weights are expected to have high entropy.

### Model Metadata Scanner

**Purpose:** perform basic static inspection of model-specific file formats.

GGUF coverage:

- validates GGUF magic bytes;
- extracts basic GGUF version where available;
- flags unusually small GGUF files.

Safetensors coverage:

- reads the safetensors header length;
- parses the JSON header;
- counts tensors;
- samples tensor names;
- inspects metadata for suspicious values;
- flags malformed or unusually large headers.

Current limitation: this scanner does not fully validate tensor offsets, tensor shapes or full GGUF key-value metadata.

### Pickle Heuristic Scanner

**Purpose:** provide an additional static check for risky pickle-like markers in high-risk serialisation formats.

Checks include suspicious markers associated with:

- shell execution;
- subprocess use;
- `eval`;
- `exec`;
- pickle `GLOBAL` / `REDUCE`-style behaviour.

ModelScan remains the primary specialised scanner for model serialisation risk. The native pickle heuristic scanner is an additional defensive check.

### Git Provenance Scanner

**Purpose:** collect basic local repository provenance evidence.

Checks include:

- whether the target is inside a Git repository;
- current commit hash;
- origin remote;
- dirty worktree status;
- Git LFS file listing where available.

Typical findings:

- dirty working tree;
- unexpected Git remote;
- missing or unavailable provenance data.

This scanner does not prove publisher trust or source authenticity.

## External Scanner Integrations

External scanner integrations are optional. If a tool is not installed, the report should show that the scanner was unavailable rather than silently omitting it.

### ModelScan

**Purpose:** specialised static scanning for unsafe model serialisation patterns.

Coverage:

- unsafe serialisation signatures;
- supported model file formats;
- skipped file reporting where supported.

Limitations:

- format coverage depends on ModelScan support;
- a clean result does not prove the model is safe;
- sophisticated evasions may not be detected.

### Semgrep

**Purpose:** static application security scanning across code and configuration.

Coverage:

- suspicious code patterns;
- known risky idioms;
- broad rule-based static analysis.

Limitations:

- depends on available rules;
- can generate false positives;
- may miss highly obfuscated logic.

### Bandit

**Purpose:** Python-specific security linting.

Coverage:

- risky Python calls;
- unsafe subprocess usage;
- insecure temporary file patterns;
- common Python security issues.

Limitations:

- Python-only;
- static analysis only;
- may overlap with native AST findings.

### pip-audit

**Purpose:** identify known vulnerabilities in Python dependency files.

Coverage:

- `requirements.txt` where present;
- known vulnerable packages and versions.

Limitations:

- depends on vulnerability database freshness;
- does not cover every package ecosystem;
- does not assess whether vulnerable code paths are reachable.

### detect-secrets

**Purpose:** detect committed secrets and credential-like values.

Coverage:

- tokens;
- private keys;
- high-entropy secret-like strings;
- common credential formats.

Limitations:

- may produce false positives;
- cannot prove no secrets exist;
- generated reports may contain sensitive evidence and should not be committed.

### Ruff, Pyright, mypy and pytest

**Purpose:** validate the quality and maintainability of this project itself.

Coverage:

- formatting;
- linting;
- type checking;
- unit and integration tests;
- CLI smoke tests.

These tools do not assess third-party model safety. They maintain the quality of the scanner project.

### CodeQL

**Purpose:** provide repository-level semantic security analysis through GitHub Actions.

Coverage:

- Python semantic code analysis;
- `security-extended` queries;
- `security-and-quality` queries;
- recurring scheduled repository analysis.

Limitations:

- only runs in GitHub Actions unless executed separately;
- primarily assesses the project code, not arbitrary downloaded model repositories;
- depends on GitHub CodeQL rule coverage.

## Reported Evidence

Scanner outputs should be preserved in two forms:

1. **Normalised findings** used by the risk scorer and Markdown/JSON reports.
2. **Raw external scanner artefacts** stored in the output directory for detailed review.

Expected report artefacts:

```text
model_due_diligence_report.md
model_due_diligence_report.json
model_due_diligence_report.sarif   # optional / planned
modelscan.json                     # when ModelScan runs
semgrep.json                       # when Semgrep runs
bandit.json                        # when Bandit runs
pip-audit-<hash>.json              # when pip-audit runs
 detect-secrets.json               # when detect-secrets runs
```

## Risk Levels

| Risk Level | Meaning | Recommended Action |
|---|---|---|
| LOW | No obvious supported static artefact risks were found | Acceptable for sandboxed first run |
| MEDIUM | Reviewable findings exist | Do not import until findings are understood |
| HIGH | Material risk indicators exist | Do not load unless every finding is justified |
| CRITICAL | Severe or multiple high-risk indicators exist | Treat as unsafe by default |

The risk score is intentionally conservative and should not be used as an automated trust verdict.

## Known Gaps

The following areas are intentionally out of scope or planned for future work:

| Gap | Status | Notes |
|---|---|---|
| Weight-level poisoning detection | Not reliably detectable | Requires behavioural, provenance and research-grade controls |
| Sleeper-agent backdoor detection | Not reliably detectable | Static artefact scanning is insufficient |
| Runtime data exfiltration testing | Not currently covered | Requires sandboxed execution harness |
| Prompt-injection behavioural testing | Planned | Especially relevant for RAG and agent use cases |
| Full GGUF metadata validation | Planned | Current coverage is header-level only |
| Full safetensors tensor validation | Planned | Current coverage focuses on header and metadata inspection |
| Licence compatibility checks | Planned | Needed for enterprise and commercial review |
| SBOM generation | Planned | Useful for release and dependency governance |
| Sigstore / SLSA provenance | Planned | Useful for stronger supply-chain attestation |
| Hugging Face API metadata checks | Planned | Should use pinned revisions and avoid implicit trust in floating tags |
| Model-card quality scoring | Planned | Should assess source, licence, intended use and limitations |

## Coverage Principles

1. **Static by default**  
   Do not load model weights or execute repository code during scanning.

2. **Evidence over assertion**  
   Findings should include category, severity, file, evidence and recommendation where practical.

3. **Conservative interpretation**  
   Suspicious artefacts should prompt review, not automatic conclusions.

4. **Normalised outputs**  
   All scanners should feed a common finding model so reports and risk scoring remain consistent.

5. **Raw evidence retention**  
   External scanner outputs should be preserved for detailed review.

6. **No false assurance**  
   Reports must state that clean results do not prove model safety.

## Summary

Current coverage is strong for practical static supply-chain checks: unsafe serialisation, suspicious code, unexpected artefacts, secrets, dependency risks, basic model metadata, Git provenance and project quality.

Current coverage is intentionally weak or absent for risks that cannot be solved reliably with static scanning alone: malicious weights, sleeper backdoors, runtime exfiltration, prompt-injection obedience and downstream agent behaviour.
