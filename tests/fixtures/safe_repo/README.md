# Safe Fixture Repository

This directory is a deliberately harmless fixture used by the test suite for `model-due-diligence`.

It exists to exercise the CLI, inventory scanner, report generation and smoke-test path without including real model weights, executable payloads, secrets or third-party artefacts.

## Contents

| File | Purpose |
|---|---|
| `README.md` | Documents why this fixture exists |
| `model.gguf.fake` | Harmless text file with a model-like name used for inventory and report-generation tests |

## Safety Notes

- This fixture does not contain a real model.
- `model.gguf.fake` is not a valid GGUF file.
- No file in this directory should be loaded by a model runtime.
- No file in this directory should require network access or external credentials.

## Expected Use

The smoke test should be able to run safely with external scanners disabled:

```zsh
mdd tests/fixtures/safe_repo \
  --out ./audit-smoke \
  --fail-on critical \
  --skip-external
```

A clean or low-risk result for this fixture is only a test assertion. It is not evidence that any real model artefact is safe.
