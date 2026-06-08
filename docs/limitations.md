# Limitations

## Purpose

`model-due-diligence` reduces practical supply-chain risk when assessing local AI model files and cloned model repositories. It does this through static inspection, provenance checks, external scanner integrations, risk scoring and reviewable reports.

It does **not** prove that a model is safe.

A clean report means only that this tool did not identify the specific static artefact risks it is designed to detect. It must not be treated as a guarantee that model weights, repository content, runtime behaviour or downstream use are benign.

## What the Tool Can Help Detect

The tool is intended to help identify evidence of:

| Risk Area | Example Signals |
|---|---|
| Unsafe serialisation | Pickle, PyTorch `.bin`, `.pt`, `.pth`, joblib, H5 or other high-risk formats |
| Suspicious repository content | Shell scripts, executable files, compiled binaries, symlinks or unexpected artefacts |
| Suspicious code patterns | `eval`, `exec`, `pickle.load`, `os.system`, `subprocess`, network calls or obfuscation |
| Secret exposure | Tokens, private keys, `.env` content or credential-like strings |
| Weak provenance | Dirty Git tree, missing source links, unexpected remotes or unpinned artefacts |
| Malformed metadata | Invalid GGUF magic bytes, malformed safetensors headers or unusual metadata |
| Dependency risk | Vulnerable Python dependencies in files such as `requirements.txt` |
| Project quality issues | Ruff, Pyright, mypy, pytest and CodeQL findings in this repository |

These checks are useful, but they are partial evidence only.

## What the Tool Cannot Reliably Detect

Static scanning cannot reliably detect:

- malicious behaviour encoded directly into model weights;
- sleeper-agent or trigger-based model backdoors;
- training-data poisoning;
- benchmark-specific manipulation;
- fine-tuning-time or adapter-level behavioural changes;
- malicious behaviour that appears only after tool integration;
- all unsafe deserialisation evasions;
- all obfuscated payloads;
- prompt-injection obedience in downstream RAG or agent workflows;
- data exfiltration behaviour that only appears during runtime;
- vulnerable behaviour introduced by the model runtime itself;
- misuse caused by unsafe prompts, tools, permissions or deployment configuration.

These risks require additional controls beyond this tool.

## Static Scanning Limitations

The tool is static by design. It should not load model weights, import untrusted repository code or execute model-specific scripts during normal scanning.

This design reduces local execution risk, but it means the tool cannot directly observe runtime behaviour. It can inspect artefacts, metadata and code patterns; it cannot fully determine what the model will do when prompted, connected to tools or deployed in an agentic workflow.

## External Scanner Limitations

External tools such as ModelScan, Semgrep, Bandit, pip-audit, detect-secrets and CodeQL improve coverage, but each has false-positive and false-negative risk.

Important limitations:

- scanner results depend on the installed version and rule set;
- unsupported formats may be skipped;
- obfuscated payloads may evade static rules;
- vulnerability databases may lag new disclosures;
- a non-zero scanner exit code does not always mean malicious content;
- a zero scanner exit code does not mean the artefact is safe.

Raw scanner output should be reviewed alongside the normalised findings.

## GGUF and Safetensors Limitations

GGUF and safetensors are generally safer operational formats than pickle-based artefacts because they are designed for model data rather than arbitrary code execution.

However:

- safer format does not mean safe model;
- metadata can still be malformed or misleading;
- files can still be tampered with;
- quantised files may be unofficial conversions;
- model weights may still contain poisoned or backdoored behaviour;
- the runtime loading the file may still have vulnerabilities.

Format choice reduces one class of risk. It does not eliminate supply-chain risk.

## Provenance Limitations

Provenance checks can indicate whether a model repository appears to come from an expected source, has a pinned commit and has a clean local state.

They cannot prove:

- the publisher account has not been compromised;
- the original model has not been poisoned;
- a quantised derivative faithfully represents the source model;
- the licence is suitable for every commercial or regulated use case;
- future downloads from the same tag will remain identical unless hashes or commits are pinned.

For serious use, pin exact revisions and record SHA-256 hashes of model artefacts.

## Risk Score Limitations

The risk score is a decision aid, not an automated trust verdict.

| Risk Level | Interpretation |
|---|---|
| LOW | No obvious supported static artefact risks were found |
| MEDIUM | Findings require review before import or execution |
| HIGH | Material risk indicators are present; do not load unless justified |
| CRITICAL | Treat as unsafe by default until proven otherwise |

The score should not be used as the sole basis for approving a model. Human review is still required, especially for high-impact, regulated, client-facing or internet-connected deployments.

## Recommended Compensating Controls

Use this tool as one control within a broader model supply-chain process:

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

Additional controls to consider:

- use official publisher repositories where possible;
- avoid `trust_remote_code=True` unless repository code has been reviewed;
- run first inference in a network-disabled container or VM;
- keep secrets, API keys, SSH keys and cloud credentials out of the runtime;
- restrict model access to local directories;
- compare behaviour against a known-good baseline model;
- test prompt-injection resistance for RAG and agent use cases;
- document licence and intended-use constraints;
- retain audit reports and hashes for reproducibility.

## Appropriate Use

This tool is appropriate for:

- pre-import review of local model files;
- cloned Hugging Face repository inspection;
- local Ollama, llama.cpp, LM Studio and Transformers due diligence;
- CI checks for scanner code quality;
- generating reviewable evidence before first execution;
- identifying artefacts that require manual inspection.

## Inappropriate Use

Do not use this tool as the sole approval mechanism for:

- regulated production deployment;
- client-data processing;
- internet-connected agentic systems;
- autonomous coding agents with write access;
- systems with access to secrets or privileged infrastructure;
- safety-critical, medical, legal, financial or high-impact decisions.

Those contexts require additional governance, testing, isolation and approval controls.

## Required User Judgement

A finding is not proof of compromise. Absence of findings is not proof of safety.

The reviewer must still decide whether:

- the source is trustworthy;
- the file types are expected;
- the licence is acceptable;
- scanner warnings are explainable;
- model behaviour is appropriate for the intended use;
- runtime isolation is adequate;
- the residual risk is acceptable.

## Summary

`model-due-diligence` should be used as a conservative evidence-gathering gate before loading or importing model artefacts.

It materially improves review discipline, but it cannot remove the need for provenance verification, sandboxing, behavioural testing, runtime controls and human judgement.
