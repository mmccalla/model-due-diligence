## Summary

## Checks
- [ ] Ruff
- [ ] Pyright
- [ ] mypy
- [ ] pytest

## Summary

Briefly describe what changed and why.

## Change Type

- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation
- [ ] CI / release / repository maintenance
- [ ] Security / supply-chain hardening
- [ ] Test-only change

## Scope

- [ ] CLI behaviour changed
- [ ] Native scanner changed
- [ ] External scanner integration changed
- [ ] Risk scoring changed
- [ ] Reporting output changed
- [ ] Packaging / dependency configuration changed
- [ ] GitHub Actions / repository automation changed
- [ ] No runtime behaviour changed

## Quality Gates

- [ ] `ruff format --check src tests`
- [ ] `ruff check src tests`
- [ ] `pyright`
- [ ] `mypy src tests`
- [ ] `pytest`
- [ ] `mdd tests/fixtures/safe_repo --out ./audit-smoke --fail-on critical --skip-external`

## Security and Supply-Chain Review

- [ ] No secrets, tokens, credentials, private keys or client data have been committed
- [ ] No unreviewed executable files, shell scripts, binaries or model artefacts have been added
- [ ] New or changed dependencies are justified and limited to the required scope
- [ ] Scanner findings, risk-score behaviour and report-output changes have been reviewed
- [ ] Any security-relevant limitations or false-positive/false-negative risks are documented

## Release Impact

- [ ] No release impact
- [ ] Version bump required
- [ ] README / docs update required
- [ ] PyPI release notes required
- [ ] GitHub release notes required

## Evidence

Add relevant command output, screenshots, report snippets or links to generated CI artefacts.

## Reviewer Notes

Highlight anything that needs careful review, including trade-offs, known limitations, edge cases or follow-up work.