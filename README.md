# Model Due Diligence

Static due-diligence scanner for local AI model artefacts and repositories.

This tool reduces supply-chain risk. It does **not** prove a model is safe.

## What it checks

- File inventory, SHA-256 hashes, permissions and symlinks
- High-risk serialisation formats such as pickle, `.pt`, `.pth`, `.bin`, `.joblib` and H5
- Lower-risk model formats such as `.gguf`, `.safetensors` and `.onnx`
- GGUF magic/version metadata
- Safetensors header metadata
- Suspicious text and binary strings
- Python AST indicators such as `eval`, `exec`, `pickle.loads` and `subprocess`
- Git provenance, remote URL, current commit and dirty worktree
- External scanner integration: ModelScan, Semgrep, Bandit, pip-audit and detect-secrets
- Optional quality self-checks using Ruff, Pyright and mypy

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,scanners]"
```

## Quick start

```bash
mdd ./downloaded-model --out ./audit
mdd ~/models/qwen.gguf --out ./audit-qwen
mdd ./downloaded-model --out ./audit --fail-on medium
```

## Development

```bash
ruff format src tests
ruff check src tests
pyright
mypy src tests
pytest
```

## Outputs

```text
audit/
├── model_due_diligence_report.md
├── model_due_diligence_report.json
├── model_due_diligence_report.sarif
├── modelscan.json
├── semgrep.json
├── bandit.json
├── pip-audit-<hash>.json
└── detect-secrets.json
```

## Limitations

A clean report does not mean a model is safe. Static checks cannot reliably detect subtle weight-level backdoors, sleeper-agent behaviour, poisoned training data, malicious behaviour activated by rare prompts, or every deserialisation evasion.

Use this tool as part of a wider control set: official or reputable sources, pinned commits and hashes, sandboxed first execution, no mounted credentials, no network for first-run testing, and adversarial behavioural tests.
