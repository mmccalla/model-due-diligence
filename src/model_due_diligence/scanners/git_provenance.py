"""Git provenance scanner.

This scanner collects local Git provenance evidence for cloned model
repositories. It records commit, remote, worktree status and Git LFS metadata
where available. These checks support review; they do not prove publisher trust
or artefact authenticity.
"""

from __future__ import annotations

from typing import Any

from model_due_diligence.domain.models import Finding, ScanContext, Severity
from model_due_diligence.external.command_runner import run_command


class GitProvenanceScanner:
    """Collect Git provenance metadata and related findings."""

    scanner_name = "git_provenance"
    timeout_seconds = 30
    expected_remote_indicators = ("huggingface.co", "github.com")

    def scan(self, context: ScanContext) -> tuple[list[Finding], dict[str, Any]]:
        """Return Git provenance findings and metadata for the scan root."""

        if not self._is_git_repo(context):
            return [], {"is_git_repo": False}

        metadata = self._collect_metadata(context)
        findings = self._find_provenance_risks(metadata)

        return findings, metadata

    @staticmethod
    def _is_git_repo(context: ScanContext) -> bool:
        return (context.root / ".git").exists()

    def _collect_metadata(self, context: ScanContext) -> dict[str, Any]:
        metadata: dict[str, Any] = {"is_git_repo": True}

        for key, command in self._commands().items():
            result = run_command(
                tool=f"git_{key}",
                command=command,
                cwd=context.root,
                timeout_seconds=self.timeout_seconds,
            )

            metadata[key] = result.stdout.strip() if result.available and result.exit_code == 0 else None

            if not result.available:
                metadata[f"{key}_error"] = f"Required command not available: {command[0]}"
            elif result.exit_code not in (0, None):
                metadata[f"{key}_error"] = result.stderr.strip() or result.stdout.strip() or f"Exit code {result.exit_code}"

        return metadata

    @staticmethod
    def _commands() -> dict[str, list[str]]:
        return {
            "head": ["git", "rev-parse", "HEAD"],
            "remote_origin": ["git", "remote", "get-url", "origin"],
            "status": ["git", "status", "--short"],
            "lfs_files": ["git", "lfs", "ls-files"],
        }

    def _find_provenance_risks(self, metadata: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []

        status = metadata.get("status")
        if status:
            findings.append(self._dirty_worktree_finding(str(status)))

        remote = str(metadata.get("remote_origin") or "")
        if remote and not self._remote_is_expected(remote):
            findings.append(self._unexpected_remote_finding(remote))

        if metadata.get("head") is None:
            findings.append(self._missing_head_finding(metadata))

        if metadata.get("remote_origin") is None:
            findings.append(self._missing_remote_finding(metadata))

        return findings

    def _remote_is_expected(self, remote: str) -> bool:
        return any(indicator in remote for indicator in self.expected_remote_indicators)

    def _dirty_worktree_finding(self, status: str) -> Finding:
        return Finding(
            severity=Severity.LOW,
            category="git_dirty_worktree",
            file="",
            message="Git repository has uncommitted changes.",
            evidence=status,
            recommendation="Pin and audit a clean commit hash before operational use.",
            scanner=self.scanner_name,
        )

    def _unexpected_remote_finding(self, remote: str) -> Finding:
        return Finding(
            severity=Severity.MEDIUM,
            category="unexpected_git_remote",
            file="",
            message="Git remote is not Hugging Face or GitHub.",
            evidence=remote,
            recommendation="Verify the repository origin before trusting downloaded model artefacts.",
            scanner=self.scanner_name,
        )

    def _missing_head_finding(self, metadata: dict[str, Any]) -> Finding:
        return Finding(
            severity=Severity.LOW,
            category="git_head_unavailable",
            file="",
            message="Could not determine Git commit hash.",
            evidence=str(metadata.get("head_error") or ""),
            recommendation="Record a pinned commit hash where possible for reproducibility.",
            scanner=self.scanner_name,
        )

    def _missing_remote_finding(self, metadata: dict[str, Any]) -> Finding:
        return Finding(
            severity=Severity.LOW,
            category="git_remote_unavailable",
            file="",
            message="Could not determine Git origin remote.",
            evidence=str(metadata.get("remote_origin_error") or ""),
            recommendation="Verify source provenance manually before trusting the artefact.",
            scanner=self.scanner_name,
        )
