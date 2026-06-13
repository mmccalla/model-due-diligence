# Sample Report

This sample is taken from a real scan of the bundled `tests/fixtures/suspicious_repo` fixture using native scanners only:

```zsh
mdd tests/fixtures/suspicious_repo --out ./audit-suspicious --skip-external
```

For a clean baseline, scan the safe fixture:

```zsh
mdd tests/fixtures/safe_repo --out ./audit-smoke --fail-on critical --skip-external
```

## Report Artefacts

A normal run produces:

```text
audit-suspicious/
├── model_due_diligence_report.md
├── model_due_diligence_report.json
└── model_due_diligence_report.sarif
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
| Risk level | MEDIUM |
| Risk score | 53 / 100 |
| Files scanned | 2 |
| Findings | 4 |
| High findings | 1 |
| Medium findings | 2 |
| Low findings | 1 |
| Info findings | 0 |

## Example Finding

| Severity | Category | File | Message | Recommendation |
|---|---|---|---|---|
| HIGH | `python_ast_dangerous_call` | `suspicious.py` | Dangerous call detected: os.system. | Review whether this call can execute during import, setup or model loading. |
| MEDIUM | `script_or_executable` | `suspicious.py` | Script or executable file present. | Review manually before running or importing the repository. |
| MEDIUM | `suspicious_text:shell_execution` | `suspicious.py` | Suspicious text pattern detected: shell_execution. | Review whether shell execution can occur during import, setup or model loading. |

## Example File Inventory

| Category | Extension | Executable | Size | SHA-256 | Path |
|---|---:|---:|---:|---|---|
| `dependency_or_build_file` | `.txt` | `false` | 530 | `15b331eaae186511da0b7ce135ff307d02b969a0f02d466d6eda0b7810beafa1` | `requirements.txt` |
| `script_or_executable` | `.py` | `false` | 470 | `2d9ffd93e7c4212ba4f60618048041e52341da45ee1c68355127a19ee1b2d33f` | `suspicious.py` |

## Interpretation

A MEDIUM result means reviewable findings exist. It does **not** prove that a model is malicious, but it does mean you should understand every finding before loading or importing the artefact.

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

Static scanning cannot reliably detect weight-level backdoors, sleeper-agent behaviour, training-data poisoning, or runtime-only exfiltration. See [docs/limitations.md](../docs/limitations.md).
