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
