# Sample Report

This sample is taken from a real scan of a locally installed Ollama model (`qwen3:4b`) using native scanners only:

```zsh
mdd-ollama qwen3:4b --out ./audit-qwen3-ollama --skip-external
```

Scanned path in the generated report: `ollama:qwen3:4b`. Generated UTC: `2026-08-26T14:38:59.562582+00:00`.

The Ollama server does not need to be running. `mdd-ollama` resolves the model from the local store (`~/.ollama/models` by default), stages scan-friendly filenames, then runs the same static due-diligence flow as `mdd`.

For a high-finding demo without a downloaded model, scan the bundled fixture:

```zsh
mdd tests/fixtures/suspicious_repo --out ./audit-suspicious --skip-external
```

## Report Artefacts

A normal run produces:

```text
audit-qwen3-ollama/
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
| Risk level | LOW |
| Risk score | 3 / 100 |
| Files scanned | 7 |
| Findings | 2 |
| High findings | 0 |
| Medium findings | 0 |
| Low findings | 1 |
| Info findings | 1 |

File categories: one `lower_risk_model_format` (`.gguf`) and six `other` artefacts (manifest, config, params, licence, template). Not a Git repository.

## Example Finding

| Severity | Category | File | Message | Recommendation |
|---|---|---|---|---|
| LOW | `external_scanners_skipped` |  | External scanners were skipped by CLI option. | Rerun without `--skip-external` for fuller supply-chain due diligence. |
| INFO | `lower_risk_model_format` | `model.gguf` | Lower-risk model format detected: `.gguf`. | Still verify provenance, hash and first-run sandboxing. |

## Example Model Metadata

`model.gguf` was recognised as GGUF version 3:

```json
{
  "magic": "GGUF",
  "gguf_version": 3,
  "size_bytes": 2497280480
}
```

## Example File Inventory

| Category | Extension | Executable | Size | SHA-256 | Path |
|---|---:|---:|---:|---|---|
| `other` | `.json` | `false` | 487 | `e18a783aae5525fd2852fc94c985541a77e791e034abc2d3056474d59de336fc` | `config.json` |
| `other` | `.txt` | `false` | 11338 | `d18a5cc71b84bc4af394a31116bd3932b42241de70c77d2b76d69a314ec8aa12` | `license.txt` |
| `other` | `.json` | `false` | 1036 | `aa3f07d8b8df05de227cdf80d3fdf28675384a096f154c9d854b922804a958b7` | `manifest.json` |
| `lower_risk_model_format` | `.gguf` | `false` | 2497280480 | `3e4cb14174460404e7a233e531675303b2fbf7749c02f91864fe311ab6344e4f` | `model.gguf` |
| `other` | `.json` | `false` | 1457 | `17c99fa88ced1b8fc3d8a99d3c2b5743fab8e139bb5d135d7884925bd1c17d57` | `ollama-model.json` |
| `other` | `.json` | `false` | 120 | `cff3f395ef3756ab63e58b0ad1b32bb6f802905cae1472e6a12034e4246fbbdb` | `params.json` |
| `other` | `.txt` | `false` | 1506 | `2d54db2b9bb29ce7db54fea63a891f5859603813c555b1f88b5e0994652897f9` | `template.txt` |

Hashes and sizes are those of the staged scan of this machine’s installed `qwen3:4b` tag. They can change if that tag is pulled again.

## Interpretation

A LOW result does **not** prove that a model is safe. It means only that this static due-diligence pass did not identify the supported static artefact risks it is designed to detect.

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
