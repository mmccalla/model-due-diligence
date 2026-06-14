# mdd-ui — Wireframe component tree (Phase 1b target)

Phases **1a–1c** are **complete on `main`**. Phase 1a delivers the API and interaction-state contracts below. Phase **1b.0** completed pre-frontend cleanup ([`mdd-ui-phase-1b-0.md`](mdd-ui-phase-1b-0.md)). Phases **1b** and **1c** implemented and polished this tree.

## Phase timeline

| Phase | Branch | Deliverable | Status |
|-------|--------|-------------|--------|
| 1a | `feat/mdd-ui-phase-1a` | `/api/v1/` backend, tests, operator docs | Complete on `main` |
| 1b.0 | `feat/mdd-ui-phase-1b-0` | Handoff checklist, static scaffold, contract freeze | Complete on `main` |
| 1b | `feat/mdd-ui-phase-1b` | Dashboard UI chrome (this component tree) | Complete on `main` |
| 1c | `feat/mdd-ui-phase-1c` | Preview polish, a11y, export UX, stale-report UX | Complete on `main` |

```text
AppShell
├── HeaderBar
│   ├── AppTitle                    "Model Due Diligence"
│   ├── ConnectionBadge             Ollama operational status (API / offline / error)
│   └── HealthIndicator             API reachable, version
│
├── MainLayout (two-column ≥768px, stacked on mobile)
│   │
│   ├── TargetPanel                 left / top — primary task entry
│   │   ├── TargetTabs
│   │   │   ├── OllamaTab
│   │   │   │   ├── OllamaStatusBanner    state: loading | connected | offline-fallback | error
│   │   │   │   ├── ModelPicker           state: empty | loading | populated | error
│   │   │   │   │   └── ModelRow[]        name, size, family, source badge
│   │   │   │   └── RefreshButton
│   │   │   └── PathTab
│   │   │       ├── PathInput             GGUF, safetensors, file, or directory
│   │   │       └── PathValidationHint    state: idle | validating | valid | error
│   │   │
│   │   ├── ScanOptionsDrawer             progressive disclosure (collapsed default)
│   │   │   ├── SkipExternalToggle
│   │   │   ├── TimeoutInput
│   │   │   └── FailOnSelect
│   │   │
│   │   ├── ScanPreviewCard               agentic plan preview (Phase 1c polish)
│   │   │   └── PreviewItemList           artefacts that will be inspected
│   │   │
│   │   └── ScanActionBar
│   │       ├── PreviewButton
│   │       └── RunScanButton             disabled while running / invalid target
│   │
│   └── ReportPanel               right / bottom — decision support
│       ├── ScanStatusBar         state: idle | running | success | partial | error
│       │   └── StaticScanNotice  "Static scan only — no weights loaded"
│       │
│       ├── LimitationsBanner     always visible on report (clean ≠ safe)
│       │
│       ├── RiskSummaryRow
│       │   ├── RiskGauge         score 0–100 + text band label
│       │   ├── SeverityCountCards critical / high / medium / low / info
│       │   └── ScanMetadataChip  timestamp, target, files scanned
│       │
│       ├── FindingsSection
│       │   ├── FindingsToolbar   filter by severity, scanner; sort
│       │   ├── FindingsTable     caption + th scope; keyboard navigable rows
│       │   └── EvidencePanel     expandable per row (message, evidence, recommendation)
│       │
│       ├── FileInventorySection
│       │   └── FileInventoryTable category, extension, sha256, size
│       │
│       ├── ModelMetadataSection  empty state when none extracted
│       │
│       └── ExportBar
│           ├── ExportMarkdown
│           ├── ExportJson
│           └── ExportSarif
│
└── Footer
    └── GovernanceNote            static evidence only; link to limitations doc
```

## State ownership (frontend-state-and-interaction-design)

| Surface | States |
|---------|--------|
| `ConnectionBadge` | idle, loading, success, partial_success, error |
| `ModelPicker` | idle, loading, empty, success, error |
| `PathInput` | idle, validating, success, error |
| `ScanStatusBar` | idle, running, success, partial_success, error |
| `ReportPanel` | empty (no scan yet), populated, stale (re-scan available) |

## API mapping (Phase 1a)

| Component data need | Endpoint |
|---------------------|----------|
| `HealthIndicator` | `GET /api/v1/health` |
| `ConnectionBadge`, `OllamaStatusBanner` | `GET /api/v1/ollama/status` |
| `ModelPicker` | `GET /api/v1/ollama/models` |
| `ScanPreviewCard` | `POST /api/v1/scan/preview` |
| `ReportPanel` | `POST /api/v1/scan` |
| `ExportBar` | `GET /api/v1/scan/{scan_id}/export/{format}` |
