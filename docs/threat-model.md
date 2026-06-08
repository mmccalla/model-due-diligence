# Threat Model

## Purpose

This document defines the threat model for `model-due-diligence`.

The project performs static supply-chain due diligence on local AI model files and cloned model repositories before they are imported into local runtimes such as Ollama, llama.cpp, LM Studio or Transformers.

The tool is designed to reduce practical risk from unsafe serialisation, suspicious repository content, weak provenance, accidental secret exposure, dependency vulnerabilities and malformed model metadata.

It does **not** prove that a model is safe. It provides reviewable evidence to support human judgement.

## System Under Review

`model-due-diligence` is a local Python CLI that:

1. accepts a path to a model file or model repository;
2. inventories files and hashes artefacts;
3. runs native static scanners;
4. optionally runs external scanner tools;
5. normalises findings;
6. calculates a conservative risk score;
7. writes Markdown, JSON and optional SARIF reports;
8. exits according to the configured `--fail-on` threshold.

The normal scan path must not load model weights, import untrusted repository code or execute model-specific scripts.

## Assets to Protect

| Asset | Why It Matters |
|---|---|
| User workstation | Model files may contain malicious artefacts or code designed to compromise the local machine |
| Secrets and credentials | API keys, SSH keys, GitHub tokens, cloud credentials and `.env` files could be exposed or exfiltrated |
| Source repositories | A malicious model repository could tamper with local project files or CI configuration |
| Local model runtime | Ollama, llama.cpp, LM Studio or Transformers may load unsafe artefacts if due diligence is bypassed |
| Audit reports | Reports may include sensitive paths, hashes, evidence snippets or scanner output |
| GitHub repository | CI, release workflows and dependency automation must not introduce new supply-chain risk |
| End users | Users may over-trust a clean report unless limitations are explicit |

## Trust Boundaries

```text
User / Developer
  |
  v
Local CLI process
  |
  +--> Local filesystem containing model artefacts
  |
  +--> Native static scanners
  |
  +--> Optional external scanner binaries
  |
  +--> Local output directory containing reports
  |
  +--> GitHub Actions workflows for this project
```

Important boundaries:

- downloaded model artefacts are untrusted input;
- cloned model repositories are untrusted input;
- external scanner binaries are trusted only to the extent they are installed from known sources and kept updated;
- generated reports may contain sensitive evidence and should be handled as local security artefacts;
- GitHub Actions has separate trust boundaries from local CLI execution.

## Threat Actors

| Actor | Motivation | Example Behaviour |
|---|---|---|
| Malicious model publisher | Compromise users who download and run a model | Publish model artefacts containing unsafe serialisation or malicious scripts |
| Compromised publisher account | Abuse a previously trusted source | Replace artefacts, tags or model cards with malicious versions |
| Malicious quantisation uploader | Target local LLM users | Publish tampered GGUF or derivative model files |
| Dependency attacker | Compromise the scanner project or its tooling | Poison packages or GitHub Actions dependencies |
| Careless contributor | Accidentally introduce risk | Commit secrets, large model files, binaries or unsafe scanner behaviour |
| Over-trusting user | Misinterpret a clean scan | Treat static scan output as proof that the model is safe |

## In-Scope Threats

### T1: Unsafe Serialisation Payloads

Model repositories may include pickle, PyTorch, joblib, H5 or other serialised artefacts that can execute code when loaded by downstream tools.

Controls:

- high-risk extension detection;
- ModelScan integration;
- pickle heuristic scanner;
- explicit findings for unsafe formats;
- recommendation to prefer GGUF, safetensors or ONNX where appropriate.

Residual risk:

- static scanners may miss evasive payloads;
- downstream tools may still load unsafe formats if the user ignores findings.

### T2: Malicious Repository Code

A cloned model repository may contain scripts or Python modules designed to run during setup, import or model loading.

Controls:

- script and executable detection;
- suspicious text pattern scanner;
- Python AST scanner;
- Semgrep and Bandit integrations;
- warning on `trust_remote_code=True`;
- no repository code execution during normal scanning.

Residual risk:

- obfuscated code may evade static checks;
- users may execute scripts manually after the scan.

### T3: Malicious or Unexpected Binaries

Model repositories may include compiled binaries, shared libraries or executable payloads.

Controls:

- file inventory;
- compiled binary detection;
- executable permission checks;
- binary string scanning;
- entropy scanner for unusual non-model artefacts.

Residual risk:

- binary analysis is heuristic;
- full reverse engineering is out of scope.

### T4: Accidental Secret Exposure

A model repository, fixture or generated report may contain tokens, private keys, cloud credentials or local environment data.

Controls:

- native suspicious string scanning;
- detect-secrets integration;
- pull request checklist;
- contribution guide rules;
- `.gitignore` patterns for audit reports and local environments.

Residual risk:

- secret scanners can have false negatives;
- evidence snippets in reports may contain sensitive values and require careful handling.

### T5: Weak Provenance or Tampered Artefacts

A model artefact may come from an unexpected source, unpinned revision or modified local working tree.

Controls:

- Git remote inspection;
- Git commit inspection;
- dirty worktree detection;
- Git LFS listing where available;
- SHA-256 hashes for all inventoried files;
- documentation recommending pinned commits and recorded hashes.

Residual risk:

- source account compromise cannot be ruled out;
- hashes only help if compared with a trusted expected value;
- quantised derivatives may not faithfully represent source models.

### T6: Malformed Model Metadata

A model file may have malformed or suspicious metadata that indicates corruption, tampering or unexpected format behaviour.

Controls:

- GGUF magic/version checks;
- unusually small GGUF detection;
- safetensors header parsing;
- safetensors tensor count and metadata inspection;
- malformed-header findings.

Residual risk:

- full GGUF metadata validation is not yet implemented;
- full safetensors tensor offset and shape validation is not yet implemented;
- valid metadata does not prove safe weights.

### T7: Vulnerable Dependency Files

Model repositories or this project may include dependency files with known vulnerable packages.

Controls:

- pip-audit integration for `requirements.txt`;
- Dependabot for repository dependencies and GitHub Actions;
- CI quality checks;
- contribution rules for dependency additions.

Residual risk:

- vulnerability databases can lag disclosures;
- not all ecosystems are covered;
- reachability is not determined.

### T8: Scanner Project Compromise

The scanner project itself could introduce vulnerabilities through poor code quality, risky dependencies or compromised workflows.

Controls:

- Ruff formatting and linting;
- Pyright and mypy type checking;
- pytest unit and integration tests;
- CodeQL scheduled and event-driven analysis;
- least-privilege GitHub Actions permissions;
- release artefact validation with `twine check`;
- PyPI trusted publishing using OIDC;
- Dependabot grouped minor/patch updates.

Residual risk:

- CI tools and GitHub Actions are third-party dependencies;
- maintainers must still review dependency and workflow changes carefully.

### T9: False Assurance

Users may treat a clean scan as proof that a model is safe.

Controls:

- limitations documented in README, architecture, scanner coverage and report text;
- conservative risk language;
- explicit statement that static scanning cannot prove benign weights;
- appropriate/inappropriate use guidance.

Residual risk:

- users may still over-trust static scanning despite warnings.

## Out-of-Scope Threats

The following are not reliably solved by this tool:

- malicious behaviour encoded directly into model weights;
- sleeper-agent or trigger-based model backdoors;
- training-data poisoning;
- benchmark-specific manipulation;
- malicious behaviour that appears only after fine-tuning;
- malicious behaviour that appears only when tools are connected;
- prompt-injection obedience in downstream RAG or agent workflows;
- data exfiltration during live inference;
- vulnerabilities in local model runtimes;
- host compromise that already occurred before scanning;
- legal or commercial licence adjudication.

These risks require additional controls such as provenance verification, sandboxed execution, behavioural testing, runtime monitoring, restricted credentials, licence review and human approval.

## Abuse Cases

| Abuse Case | Expected Tool Response |
|---|---|
| Repository contains `.pkl` with unsafe payload indicators | High or critical finding; do not load unless fully justified |
| Repository contains `setup.sh` downloading and executing remote code | Medium/high finding from script detection and text patterns |
| Repository contains `model.gguf` with invalid magic bytes | High finding; redownload or reject artefact |
| Repository contains `.env` or API token in README | Secret finding; remove and rotate credential if real |
| Repository uses `trust_remote_code=True` in example code | High finding or review warning depending on context |
| Repository has unexpected remote origin | Medium provenance finding |
| Model passes static checks but behaves maliciously at runtime | Out of scope; requires sandboxed behavioural testing |

## Security Requirements

The project should maintain the following requirements:

1. The normal scan path must not execute model files or repository code.
2. The tool must produce reviewable findings with severity, category, file and recommendation where practical.
3. External scanner unavailability must be visible in reports.
4. Generated reports must not be automatically committed.
5. CI must run formatting, linting, type checking, tests and smoke tests.
6. CodeQL must run on pull requests, pushes, manual dispatch and a scheduled cadence.
7. Release publishing must use least-privilege permissions and trusted publishing where possible.
8. Documentation must preserve the limitation that clean scans are not proof of safety.

## Recommended User Controls

Use `model-due-diligence` as one layer in a broader process:

```text
Official or reputable source
+ pinned commit or hash
+ static due-diligence scan
+ first run in a no-network sandbox
+ no credentials mounted
+ restricted filesystem access
+ adversarial behavioural test suite
+ runtime monitoring
+ human review
= reasonable practical risk reduction
```

Operational recommendations:

- prefer official publisher repositories or reputable quantisers;
- avoid floating tags such as `latest` for operational use;
- record SHA-256 hashes of accepted artefacts;
- do not load high-risk serialisation formats unless the source and need are clear;
- avoid `trust_remote_code=True` unless repository code has been reviewed;
- run first inference in a network-disabled container or VM;
- keep API keys, SSH keys, cloud tokens and client data out of the runtime;
- review generated reports before sharing or committing them.

## Residual Risk Summary

| Risk | Residual Level | Reason |
|---|---|---|
| Unsafe serialisation | Medium | Scanners reduce risk but evasions remain possible |
| Suspicious repository code | Medium | Static rules may miss obfuscation |
| Secret exposure | Medium | Detection is pattern-based and imperfect |
| Weak provenance | Medium | Source trust cannot be proven locally |
| Malformed metadata | Low/Medium | Basic checks exist but full validation is incomplete |
| Weight-level backdoors | High | Not reliably detectable through static scanning |
| Runtime exfiltration | High | Requires sandboxed runtime testing |
| False assurance | Medium | Documentation helps but user judgement is still required |

## Review Cadence

Review this threat model when:

- a new scanner is added;
- risk scoring changes;
- report semantics change;
- new model formats are supported;
- external scanner dependencies change materially;
- release or CI workflows are changed;
- the project begins supporting runtime behavioural tests.

## Summary

The main threats are unsafe serialisation, malicious repository content, weak provenance, accidental secret exposure, dependency risk and false assurance.

The project mitigates these through static inspection, external scanner integrations, conservative risk scoring, reviewable reports and hardened repository automation.

The highest residual risks remain model-weight backdoors, runtime behaviour and user over-trust of clean static results.
