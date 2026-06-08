# Sample Report

Run `mdd tests/fixtures/safe_repo --out ./audit` to generate a real report.

# Sample Model Due Diligence Report

This sample illustrates the expected shape of a generated `model-due-diligence` Markdown report.

It is not a real scan result. Generate a real report with:

```zsh
mdd tests/fixtures/safe_repo --out ./audit-smoke --fail-on critical --skip-external
```

For a fuller local scan that includes optional external scanners, run:

```zsh
mdd tests/fixtures/suspicious_repo --out ./audit-suspicious --fail-on high
```

## Report Artefacts

A normal run should produce:

```text
audit-smoke/
├── model_due_diligence_report.md
├── model_due_diligence_report.json
└── model_due_diligence_report.sarif   # optional / planned
```

When external scanners run, additional raw evidence files may also be present:

```text
modelscan.json
semgrep.json
bandit.json
pip-audit-<hash>.json
detect-secrets.json
```

## Example Summary

| Field | Example Value |
|---|---:|
| Risk level | LOW |
| Risk score | 3 / 100 |
| Files scanned | 2 |
| Findings | 1 |
| High findings | 0 |
| Medium findings | 0 |
| Low findings | 0 |
| Info findings | 1 |

## Example Finding

| Severity | Category | File | Message | Recommendation |
|---|---|---|---|---|
| INFO | `lower_risk_model_format` | `model.gguf.fake` | Lower-risk model-like format detected. | Verify provenance, hash and first-run sandboxing before operational use. |

## Example File Inventory

| Category | Extension | Executable | Size | SHA-256 | Path |
|---|---:|---:|---:|---|---|
| `other` | `.md` | `false` | 128 | `<sha256>` | `README.md` |
| `lower_risk_model_format` | `.fake` | `false` | 64 | `<sha256>` | `model.gguf.fake` |

## Interpretation

A LOW result does not prove that a model is safe. It means only that this static due-diligence pass did not identify the supported static artefact risks it is designed to detect.

Before loading or importing any model artefact, use the broader control pattern:

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

## Known Limitations

Static scanning cannot reliably detect:

- malicious behaviour encoded directly into model weights;
- sleeper-agent or trigger-based backdoors;
- training-data poisoning;
- all unsafe deserialisation evasions;
- prompt-injection obedience in downstream RAG or agent workflows;
- data exfiltration behaviour that only appears during runtime.

Use generated reports as review evidence, not as an automated trust verdict.