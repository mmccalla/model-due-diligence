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

### First release (project not yet on PyPI)

If `model-due-diligence` does not exist on PyPI yet, register a **pending publisher** before re-running the release workflow:

1. Sign in to [PyPI](https://pypi.org/).
2. Open **Account settings** → **Publishing** → **Add a new pending publisher**.
3. Set:
   - **PyPI project name:** `model-due-diligence`
   - **Owner:** `mmccalla`
   - **Repository name:** `model-due-diligence`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
4. Save the pending publisher.

On GitHub, create the matching environment:

1. Open **Settings** → **Environments** → **New environment** named `pypi`.
2. Optionally require manual approval for the publish job.

Push or re-run the tag workflow after both sides are configured. The first successful publish creates the PyPI project.

### Existing PyPI project

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

If the **Publish to PyPI** job fails on the first release, configure the pending publisher and GitHub `pypi` environment (above), then open the failed workflow run and choose **Re-run failed jobs**.

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

## Install from GitHub release (until PyPI publish is configured)

If PyPI Trusted Publishing is not yet configured, install the v0.1.0 wheel directly from the GitHub release:

```zsh
pip install https://github.com/mmccalla/model-due-diligence/releases/download/v0.1.0/model_due_diligence-0.1.0-py3-none-any.whl
```

Then re-run or wait for the PyPI publish job after completing [`docs/publishing.md`](docs/publishing.md).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Release workflow fails on version check | Tag does not match `pyproject.toml` | Bump version or retag |
| PyPI publish job skipped | Tag does not start with `v` | Use `vX.Y.Z` tags |
| PyPI publish fails with permissions error | Trusted Publisher not configured | Complete PyPI pending publisher setup |
| Publish to PyPI job failed on first release | Pending publisher / `pypi` environment not configured | Follow [`docs/publishing.md`](docs/publishing.md), then re-run the failed job or re-push the tag |
| Quality job fails | Local gate regression | Run `./scripts/run-quality.sh` and fix before retagging |

## Manual fallback (not recommended)

If Trusted Publishing is unavailable, create a PyPI API token with upload scope and store it as `PYPI_API_TOKEN` in the `pypi` environment. Prefer Trusted Publishing for supply-chain safety.
