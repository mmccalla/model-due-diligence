# mdd-ui local dashboard API

`mdd-ui` is an optional local web API for the Model Due Diligence dashboard. It wraps the existing static scan engine and exposes versioned JSON endpoints for Phase 1b frontend work.

## Install

```zsh
pip install "model-due-diligence[ui]"
```

Development:

```zsh
pip install -e ".[dev]"
```

## Run

```zsh
mdd-ui
```

Defaults:

- bind address: `127.0.0.1`
- port: `8765`
- OpenAPI docs: `http://127.0.0.1:8765/docs`

Override bind address only for trusted local networks. The API is designed for local operator use, not public exposure.

## Security posture

- **Local bind by default** — do not expose `mdd-ui` to untrusted networks without authentication and TLS.
- **Path scans** — the API can scan paths under the operator's home directory, system temp directory, or current working directory (same intentional contract as the CLI, confined for localhost use)
- **Ollama host** — discovery uses `OLLAMA_HOST` (default `http://127.0.0.1:11434`). Pointing this at remote hosts can trigger outbound HTTP from the API process.
- **No authentication** — Phase 1a assumes a single trusted operator on localhost.
- **Report retention** — scan artefacts are stored under `~/.cache/model-due-diligence/ui-scans/` and retired after 24 hours or when the directory cap is exceeded.

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
