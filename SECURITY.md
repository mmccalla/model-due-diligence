# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes |

## Reporting a vulnerability

If you believe you have found a security vulnerability in `model-due-diligence`, please report it responsibly.

**Do not** open a public GitHub issue for security-sensitive reports.

Instead, email **markm@portantonio.co.uk** with:

1. A description of the issue and its potential impact
2. Steps to reproduce, if available
3. Any suggested remediation, if you have one

We aim to acknowledge reports within **5 business days** and will coordinate disclosure timing with you.

## Scope

This policy covers the `model-due-diligence` CLI package, its scanners, report generators and repository automation.

It does **not** cover:

- vulnerabilities in third-party scanner CLIs (ModelScan, Semgrep, Bandit, etc.);
- vulnerabilities in model runtimes (Ollama, llama.cpp, Transformers, etc.);
- malicious model weights or runtime behaviour that static scanning cannot detect.

## Safe use

- Do not mount credentials when scanning untrusted model artefacts
- Treat generated reports as review evidence, not proof of safety
- Run first inference in a network-disabled sandbox

## mdd-ui localhost-only posture

The optional `mdd-ui` dashboard (`model-due-diligence[ui]`) is a **localhost-only operator tool**. It is not designed for internet-facing or multi-tenant deployment.

- `mdd-ui` binds to **127.0.0.1** by default; keep it on loopback unless you have a deliberate, reviewed reason to change `--host`.
- Do not expose `mdd-ui` on `0.0.0.0`, a public interface, or behind an unauthenticated reverse proxy.
- Scan targets and API requests are operator-controlled; treat the UI as privileged local access to filesystem scan roots under the same constraints as the CLI.

## Audit reports and PII

Generated audit outputs can contain **PII and sensitive metadata** from scanned targets, including:

- absolute filesystem paths (home directories, usernames, project layout);
- hostnames, repository URLs, and environment-specific identifiers;
- code snippets, dependency names, and scanner evidence.

Reports include files such as `model_due_diligence_report.*`, directories named `audit*`, raw scanner JSON (for example `pip-audit-*.json`), and `mdd-ui` scan artefacts under `~/.cache/model-due-diligence/ui-scans/` by default.

Handle these outputs as confidential review evidence. Redact or avoid sharing them outside your trust boundary.

## Never commit audit outputs

**Never commit audit or scanner output to git** (or attach them to issues, PRs, or CI artefacts).

- Keep outputs in ignored local directories (for example `./audit-smoke/` during development).
- Install repository hooks to block accidental commits: `./scripts/setup-git-hooks.sh`
- Review generated files for sensitive content before any manual copy or upload.
