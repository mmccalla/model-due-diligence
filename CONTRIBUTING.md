# Contributing

Thank you for your interest in contributing to `model-due-diligence`.

Please read the full [contribution guide](docs/contribution-guide.md) before opening a pull request.

## Quick start

```zsh
./scripts/dev-setup.sh
source .venv/bin/activate
./scripts/run-quality.sh
```

## Git commit hygiene

Do not add tool attribution to commits or pull requests:

- No `Co-authored-by: Cursor <cursoragent@cursor.com>` or similar AI/tool trailers
- No `Made-with: Cursor` lines in commits, PR bodies, or review comments

After cloning, install the commit hook:

```zsh
./scripts/setup-git-hooks.sh
```

If you use Cursor, disable **Settings → Agents → Attribution** (commit and PR attribution).

## Pull request checklist

- [ ] `./scripts/run-quality.sh` passes locally
- [ ] Behaviour changes include tests
- [ ] Security and limitation implications are documented where relevant
- [ ] Scanners remain static by default (no execution of untrusted model artefacts)

## Code of conduct

Be respectful, precise and evidence-led. This project handles supply-chain security; claims must match what the tool can actually detect.
