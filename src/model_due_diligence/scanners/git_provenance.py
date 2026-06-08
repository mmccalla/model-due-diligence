from __future__ import annotations

from typing import Any

from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.external.command_runner import run_command


class GitProvenanceScanner:
    def scan(self, context: ScanContext) -> tuple[list[Finding], dict[str, Any]]:
        if not (context.root / ".git").exists():
            return [], {"is_git_repo": False}
        metadata: dict[str, Any] = {"is_git_repo": True}
        findings: list[Finding] = []
        commands = {"head": ["git", "rev-parse", "HEAD"], "remote_origin": ["git", "remote", "get-url", "origin"], "status": ["git", "status", "--short"], "lfs_files": ["git", "lfs", "ls-files"]}
        for key, command in commands.items():
            result = run_command(f"git_{key}", command, cwd=context.root, timeout_seconds=30)
            metadata[key] = result.stdout.strip() if result.available and result.exit_code == 0 else None
        if metadata.get("status"):
            findings.append(Finding(Severity.LOW, "git_dirty_worktree", "", "Git repository has uncommitted changes.", evidence=metadata["status"]))
        remote = metadata.get("remote_origin") or ""
        if remote and not ("huggingface.co" in remote or "github.com" in remote):
            findings.append(Finding(Severity.MEDIUM, "unexpected_git_remote", "", "Git remote is not Hugging Face or GitHub.", evidence=remote))
        return findings, metadata
