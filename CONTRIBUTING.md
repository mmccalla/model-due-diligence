# Contributing

Thank you for your interest in contributing to `model-due-diligence`.

Please read the full [contribution guide](docs/contribution-guide.md) before opening a pull request.

## Quick start

```zsh
./scripts/dev-setup.sh
source .venv/bin/activate
./scripts/run-quality.sh
```

## Pull request checklist

- [ ] `./scripts/run-quality.sh` passes locally
- [ ] Behaviour changes include tests
- [ ] Security and limitation implications are documented where relevant
- [ ] Scanners remain static by default (no execution of untrusted model artefacts)

## Code of conduct

Be respectful, precise and evidence-led. This project handles supply-chain security; claims must match what the tool can actually detect.
