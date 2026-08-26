# Sample Report

This sample is taken from a real scan of a locally installed Ollama model from Hugging Face (`hf.co/Qwen/Qwen3-8B-GGUF:Q4_K_M`) using native scanners only:

```zsh
mdd-ollama hf.co/Qwen/Qwen3-8B-GGUF:Q4_K_M --out ./audit-qwen3-8b-gguf --skip-external
```

Scanned path in the generated report: `ollama:hf.co/Qwen/Qwen3-8B-GGUF:Q4_K_M`. Generated UTC: `2026-08-26T17:05:46.285797+00:00`.

The Ollama server does not need to be running. `mdd-ollama` resolves the model from the local store (`~/.ollama/models` by default), stages scan-friendly filenames, then runs the same static due-diligence flow as `mdd`.

For the library `qwen3:4b` sample, see [sample-report-qwen3-4b.md](sample-report-qwen3-4b.md). For a high-finding demo without a downloaded model, scan the bundled fixture:

```zsh
mdd tests/fixtures/suspicious_repo --out ./audit-suspicious --skip-external
```

## Report Artefacts

A normal run produces:

```text
audit-qwen3-8b-gguf/
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
  "size_bytes": 5027783488
}
```

## Example File Inventory

| Category | Extension | Executable | Size | SHA-256 | Path |
|---|---:|---:|---:|---|---|
| `other` | `.json` | `false` | 700 | `8f0bcb29bd5498f04f99dd310b34c2e39516c631a926748dcc9eb0f3d34c44a9` | `config.json` |
| `other` | `.txt` | `false` | 11544 | `5de36594c10839788a8c589443a8ef9d8b8d17c65a1b5807206ae037fc36c6bd` | `license.txt` |
| `other` | `.json` | `false` | 1036 | `1ee0dfb721ea80a277bf40b5e23d9bdf52a123a8b863f2c626bd7ba89f96f6b7` | `manifest.json` |
| `lower_risk_model_format` | `.gguf` | `false` | 5027783488 | `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785` | `model.gguf` |
| `other` | `.json` | `false` | 1476 | `66c7e0e2c7699270aee1a2da46963879072cec79ea4b05d0171d980d5879727d` | `ollama-model.json` |
| `other` | `.json` | `false` | 270 | `52610851456960402dc4ce4966dbea0eb83bb1d72c3eeeaefaafe09b4690ad9c` | `params.json` |
| `other` | `.txt` | `false` | 1506 | `2d54db2b9bb29ce7db54fea63a891f5859603813c555b1f88b5e0994652897f9` | `template.txt` |

Hashes and sizes are those of the staged scan of this machine’s installed `hf.co/Qwen/Qwen3-8B-GGUF:Q4_K_M` tag. They can change if that tag is pulled again.

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
