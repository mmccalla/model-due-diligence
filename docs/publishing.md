# Publishing

This document describes how to publish `model-due-diligence` to GitHub and PyPI.

## Prerequisites

1. All quality gates pass locally:

   ```zsh
   ./scripts/run-quality.sh
   ```

2. `[project].version` in `pyproject.toml` matches the release tag (for example `0.1.0` for tag `v0.1.0`).

3. GitHub repository admin access for environments and releases.

## PyPI Trusted Publishing (recommended)

Configure PyPI to accept OIDC tokens from GitHub Actions:

1. Sign in to [PyPI](https://pypi.org/) and open **Publishing** → **Add a new pending publisher** (or edit the existing project publisher).
2. Set:
   - **PyPI project name:** `model-due-diligence`
   - **Owner:** `mmccalla`
   - **Repository name:** `model-due-diligence`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
3. Save the pending publisher configuration.

On GitHub:

1. Open **Settings** → **Environments** → **New environment** named `pypi`.
2. Optionally restrict deployment to the `main` branch and require reviewers.
3. No PyPI API token is required when using Trusted Publishing.

The release workflow (`.github/workflows/release.yml`) runs quality gates, validates the tag/version match, builds distributions, creates a GitHub release, and publishes to PyPI.

## Release steps

```zsh
git checkout main
git pull origin main
./scripts/run-quality.sh
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin main
git push origin v0.1.0
```

Monitor:

- GitHub Actions → **Release** workflow
- GitHub → **Releases**
- PyPI → https://pypi.org/project/model-due-diligence/

## Verify the published package

```zsh
python -m venv /tmp/mdd-verify
source /tmp/mdd-verify/bin/activate
python -m pip install --upgrade pip
python -m pip install model-due-diligence
mdd --help
mdd-ollama --help
deactivate
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Release workflow fails on version check | Tag does not match `pyproject.toml` | Bump version or retag |
| PyPI publish job skipped | Tag does not start with `v` | Use `vX.Y.Z` tags |
| PyPI publish fails with permissions error | Trusted Publisher not configured | Complete PyPI pending publisher setup |
| `environment pypi not found` | Missing GitHub environment | Create `pypi` environment in repo settings |
| Quality job fails | Local gate regression | Run `./scripts/run-quality.sh` and fix before retagging |

## Manual fallback (not recommended)

If Trusted Publishing is unavailable, create a PyPI API token with upload scope and store it as `PYPI_API_TOKEN` in the `pypi` environment. Prefer Trusted Publishing for supply-chain safety.
