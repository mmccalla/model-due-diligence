# Standards Alignment

This document records how `model-due-diligence` aligns with relevant guidance
from NIST, MITRE, and OWASP as of June 8, 2026.

It is a control-mapping aid, not a certification statement. The project
implements a useful subset of the controls implied by these frameworks, mostly
around static pre-deployment review, supply-chain hygiene, and reviewable
evidence.

## Scope

`model-due-diligence` is a local static due-diligence CLI. It is strongest as a
pre-ingest gate for model artefacts and cloned model repositories.

It is not:

- a runtime isolation platform;
- a full AI governance workflow system;
- a behavioural evaluation harness;
- a provenance attestation verifier;
- a full red-teaming platform.

## NIST Alignment

### NIST AI RMF 1.0 and NIST AI 600-1 GenAI Profile

Relevant source documents:

- NIST AI RMF 1.0
- NIST AI 600-1, Artificial Intelligence Risk Management Framework:
  Generative Artificial Intelligence Profile

Current project alignment:

- `Map`: the repo documents intended use, threat model, limitations, trust
  boundaries, and residual risk in [threat-model.md](./threat-model.md),
  [architecture.md](./architecture.md), and [limitations.md](./limitations.md).
- `Measure`: the scanners generate deterministic evidence across file
  inventory, suspicious code, unsafe serialisation indicators, secrets,
  dependency files, Git provenance, and model metadata.
- `Manage`: the CLI produces bounded risk scores, risk levels, machine-readable
  reports, and configurable failure thresholds for review and gating.
- Trustworthiness support:
  - validity and reliability: deterministic static checks and stable JSON/SARIF
    output;
  - safety and security: non-execution design, subprocess isolation,
    suspicious-pattern detection, dependency scanning hooks, and provenance
    checks;
  - transparency and accountability: explicit report limitations, threat-model
    documentation, and preserved external-tool evidence.

Gaps against fuller AI RMF adoption:

- no organisational governance workflow or approval evidence store;
- no runtime behavioural evaluation of model actions or outputs;
- no formal control ownership or risk-acceptance workflow;
- no automated model-card quality assessment;
- no end-to-end measurement of downstream misuse or deployment drift.

### NIST SSDF 1.1 and SP 800-218A

Relevant source documents:

- NIST SP 800-218, Secure Software Development Framework (SSDF) Version 1.1
- NIST SP 800-218A, Secure Software Development Practices for Generative AI and
  Dual-Use Foundation Models

Current project alignment:

- secure build and release basics:
  - CI runs formatting, linting, typing, tests, and smoke tests;
  - CodeQL is enabled for repository analysis;
  - Dependabot is enabled for Python and GitHub Actions dependencies;
  - PyPI publishing uses OIDC trusted publishing in
    [.github/workflows/release.yml](../.github/workflows/release.yml).
- secure implementation patterns:
  - scanner design avoids loading model weights or importing untrusted code;
  - subprocess execution avoids `shell=True` and sanitises inherited
    pytest/coverage environment state before external tool execution;
  - report writers are separate from scanner execution and domain models are
    kept infrastructure-free.

Gaps:

- no SBOM generation;
- no signed release or Sigstore verification;
- no provenance attestation or SLSA-style build verification;
- no dedicated secure-code review checklist mapped to SSDF tasks.

## MITRE Alignment

### MITRE ATLAS

Relevant source document:

- MITRE ATLAS, the adversarial threat landscape for AI-enabled systems

Current project alignment:

- helps identify pre-deployment artefacts associated with realistic adversary
  pathways against AI-enabled systems, including:
  - unsafe or high-risk serialisation artefacts;
  - suspicious repository code and shell-execution indicators;
  - secret exposure and credential access indicators;
  - suspicious network, download, and remote-code-loading patterns;
  - weak source provenance and modified repository state.
- provides evidence that can feed ATLAS-informed threat assessment or human red
  team review.

Gaps:

- no native ATLAS tactic/technique tagging in findings;
- no threat-emulation or red-team automation;
- no incident-sharing integration;
- no runtime detection of adversarial model behaviour, prompt attacks, or model
  theft techniques.

## OWASP Alignment

### OWASP Top 10 for LLM Applications 2025

Relevant source document:

- OWASP Top 10 for LLM Applications 2025

Current project alignment is partial because this project is not itself an LLM
application runtime. It is best understood as a secure intake and review tool.

Areas with meaningful support:

- supply-chain and dependency risk:
  - dependency-file discovery;
  - `pip-audit` integration;
  - repository and workflow hygiene;
  - explicit future gap for SBOM and provenance work.
- unsafe remote code and excessive trust:
  - detection of `trust_remote_code=True`;
  - AST and text scanning for shell execution, dynamic download-and-execute,
    and suspicious install patterns.
- secrets and sensitive data:
  - native suspicious-pattern scanning;
  - `detect-secrets` integration;
  - report guidance to rotate exposed credentials.
- insecure artefact handling:
  - detection of pickle-like and unsafe serialisation formats;
  - metadata validation for GGUF and safetensors;
  - compiled-binary and executable-file review signals.

Important OWASP gaps:

- no protection against prompt injection at runtime;
- no output-monitoring or unsafe-agent-action control plane;
- no runtime authorization or excessive-agency guardrails;
- no live data-exfiltration detection;
- no session, memory, or tool-use policy enforcement for agentic systems.

## Practical Conclusion

The project is now cohesive and functional as a static security review gate.
Its strongest standards alignment is:

- NIST AI RMF `Map`/`Measure`/`Manage`;
- NIST SSDF secure development hygiene for the scanner itself;
- MITRE ATLAS-informed pre-deployment threat review;
- OWASP LLM Top 10 supply-chain, remote-code, and artefact-risk reduction.

The biggest remaining gaps are runtime and provenance controls:

- behavioural testing in sandboxed execution;
- SBOM generation;
- Sigstore or equivalent provenance attestation verification;
- explicit ATLAS tagging in findings;
- stronger governance and approval evidence for risk acceptance.
