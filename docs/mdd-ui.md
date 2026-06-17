# mdd-ui Local Dashboard

`mdd-ui` is the optional local dashboard for Model Due Diligence. It is one FastAPI process that serves:

- the static dashboard at `/`;
- the versioned JSON API at `/api/v1/`;
- the same in-process static scan engine used by the `mdd` CLI.

It is not a distributed stack. There is no separate frontend service or backend service to run for this project. Ollama is optional: `mdd-ui` can query an Ollama-compatible API or local model store, but Ollama is not this project's backend.

## Install

Dashboard only:

```zsh
pip install "model-due-diligence[ui]"
```

Dashboard plus optional external scanner tools:

```zsh
pip install "model-due-diligence[ui,scanners,semgrep]"
```

Development from a checkout:

```zsh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,scanners,semgrep]"
```

## Run

```zsh
mdd-ui
```

Defaults:

- bind address: `127.0.0.1`
- port: `8765`
- dashboard: `http://127.0.0.1:8765/`
- OpenAPI docs: `http://127.0.0.1:8765/docs`

Override bind address only for trusted local networks. The API is designed for local operator use, not public exposure.

If another process is already using port `8765`, choose another local port:

```zsh
mdd-ui --host 127.0.0.1 --port 8766
```

For development, make sure the command resolves to the virtual environment you expect:

```zsh
source .venv/bin/activate
which mdd-ui
which modelscan semgrep bandit detect-secrets pip-audit
mdd-ui --host 127.0.0.1 --port 8765
```

External scanners are discovered from the `PATH` of the `mdd-ui` process. If the dashboard is started from a global Python or `pyenv` shim that lacks scanner extras, scans will show `scanner_unavailable` findings even if a different virtual environment has the tools installed.

## Scanner behaviour

Native scanners are always part of the package. External scanners are optional command-line tools:

| Tool | Extra | Used for |
|------|-------|----------|
| ModelScan | `scanners` | Unsafe model serialisation checks |
| Bandit | `scanners` | Python security linting |
| detect-secrets | `scanners` | Secret pattern detection |
| pip-audit | `scanners` | Python dependency vulnerability checks |
| Semgrep | `semgrep` | Static application/security pattern checks |

When an external scanner is missing, unavailable or exits non-zero, the report records that explicitly. This is intentional: missing evidence must be visible rather than silently ignored.

For a lightweight scan, enable `skip_external` in the UI options. For fuller local coverage, install and run the dashboard from:

```zsh
python -m pip install -e ".[dev,scanners,semgrep]"
```

If editable package metadata becomes stale after local development, verify and refresh it:

```zsh
python -c "import model_due_diligence; print(model_due_diligence.__version__)"
python -m pip install --ignore-installed -e ".[dev,scanners,semgrep]"
```

## Security posture

- **Local bind by default** — do not expose `mdd-ui` to untrusted networks without authentication and TLS.
- **Path scans** — the API can scan paths under the operator's home directory, system temp directory, or current working directory (same intentional contract as the CLI, confined for localhost use)
- **Ollama host** — discovery uses `OLLAMA_HOST` (default `http://127.0.0.1:11434`). Pointing this at remote hosts can trigger outbound HTTP from the API process.
- **No authentication** — Phase 1a assumes a single trusted operator on localhost.
- **Report retention** — scan artefacts are stored under `~/.cache/model-due-diligence/ui-scans/` and retired after 24 hours or when the directory cap is exceeded.
- **Sensitive reports** — reports may include local paths, model names, hashes, scanner output and evidence snippets. Keep them local unless reviewed.

## API version

All routes are versioned under `/api/v1/`.

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | API and scanner-engine readiness |
| `GET /api/v1/ollama/status` | Ollama connectivity and discovery mode |
| `GET /api/v1/ollama/models` | Installed Ollama models |
| `POST /api/v1/scan/preview` | Static scan plan preview |
| `POST /api/v1/scan` | Run static scan and return serialised report |
| `GET /api/v1/scan/{scan_id}/export/{format}` | Download `markdown`, `json`, or `sarif` report |

OpenAPI schema: `GET /openapi.json`.

## Interaction states

Responses include an explicit `state` field so the frontend does not infer status from missing data.

Supported values:

- `idle`, `loading`, `running`
- `success`, `partial_success`, `warning`, `empty`, `error`

`partial_success` is returned when one or more external tools were unavailable or exited non-zero. `warning` is returned when the scan completed but configuration warnings apply (for example `skip_external=true`).

## Error contract

Client and validation failures return HTTP `4xx` with a structured body:

```json
{
  "state": "error",
  "error": "target_not_found",
  "detail": "Target does not exist: /tmp/missing"
}
```

Preview and scan endpoints use the same error semantics.

## Scan output lifecycle

Each `POST /api/v1/scan` allocates:

- `scan_id` — 32-character hex identifier returned in `report_paths.scan_id`
- `output_dir` — on-disk directory under the cache root

Export downloads use `scan_id` and remain available until retention cleanup runs.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama HTTP API base URL |
| `OLLAMA_MODELS` | `~/.ollama/models` | Local model store for filesystem fallback |

## Compatibility

Phase 1a introduced `/api/v1/`. Breaking changes to request or response schemas require a new API version prefix and documentation in this file.

## Related docs

- Wireframe component tree: [`ui-component-tree.md`](ui-component-tree.md)
- Scope and limitations: [`limitations.md`](limitations.md)
