
"""Suspicious pattern definitions used by native scanners.

These patterns are intentionally conservative. A match is evidence for manual
review, not proof of compromise. Keep this module declarative: scanners should
import these constants and own the matching/reporting behaviour.
"""

from __future__ import annotations

SUSPICIOUS_TEXT_PATTERNS: dict[str, str] = {
    "shell_execution": r"\b(os\.system|subprocess\.|popen\(|exec\(|eval\(|compile\()",
    "network_access": (
        r"\b(requests\.|urllib\.|httpx\.|socket\.|ftplib\.|paramiko\.|scp\b|ssh\b|sftp\b|"
        r"curl\b|wget\b|Invoke-WebRequest\b|Start-BitsTransfer\b)"
    ),
    "destructive_file_ops": (
        r"\b(rm\s+-rf|shred\b|dd\s+if=|mkfs\b|diskutil\b|shutil\.rmtree|chmod\s+\+x|"
        r"chown\b|unlink\(|remove\(|Delete-Item\b|Remove-Item\b)"
    ),
    "secret_terms": (
        r"\b(AWS_SECRET|AWS_ACCESS|AWS_SESSION_TOKEN|OPENAI_API_KEY|HF_TOKEN|HUGGINGFACE_TOKEN|"
        r"GITHUB_TOKEN|GITLAB_TOKEN|PRIVATE_KEY|BEGIN RSA|BEGIN OPENSSH|BEGIN PRIVATE KEY|"
        r"AZURE_CLIENT_SECRET|GOOGLE_APPLICATION_CREDENTIALS|password|passwd|secret|token)\b"
    ),
    "obfuscation": (
        r"\b(base64\.b64decode|fromhex\(|codecs\.decode|marshal\.loads|pickle\.loads|"
        r"cloudpickle\.loads|dill\.loads|__import__\()"
    ),
    "environment_access": r"\b(os\.environ|getenv\(|printenv\b|env\s*\||Get-ChildItem\s+Env:)\b",
    "reverse_shell": (
        r"\b(/bin/sh|/bin/bash|/bin/zsh|nc\s+-e|ncat\s+-e|bash\s+-i|sh\s+-i|"
        r"pty\.spawn|powershell\s+-enc|powershell\s+-nop|cmd\.exe\s*/c)"
    ),
    "package_install": (
        r"\b(pip\s+install|python\s+-m\s+pip\s+install|npm\s+install|pnpm\s+install|"
        r"yarn\s+add|curl\s+.*\|\s*(bash|sh)|wget\s+.*\|\s*(bash|sh))"
    ),
    "transformers_remote_code": r"trust_remote_code\s*=\s*True",
    "dynamic_download_and_execute": (
        r"\b(curl\b.*\|\s*(bash|sh|python)|wget\b.*\|\s*(bash|sh|python)|"
        r"Invoke-WebRequest\b.*Invoke-Expression)"
    ),
    "credential_file_access": (
        r"(\.env\b|id_rsa\b|id_ed25519\b|\.ssh/|credentials\.json\b|service-account\.json\b|"
        r"\.aws/credentials\b|\.config/gcloud\b)"
    ),
}

SUSPICIOUS_BINARY_STRINGS: dict[str, str] = {
    "url": r"https?://[^\s\"'<>]{8,}",
    "shell_path": r"/bin/(sh|bash|zsh)",
    "windows_shell": r"(powershell|cmd\.exe)",
    "env_var": (
        r"(OPENAI_API_KEY|HF_TOKEN|HUGGINGFACE_TOKEN|GITHUB_TOKEN|GITLAB_TOKEN|AWS_SECRET_ACCESS_KEY|"
        r"AWS_ACCESS_KEY_ID|AWS_SESSION_TOKEN|AZURE_CLIENT_SECRET|GOOGLE_APPLICATION_CREDENTIALS)"
    ),
    "private_key_marker": r"(BEGIN RSA PRIVATE KEY|BEGIN OPENSSH PRIVATE KEY|BEGIN PRIVATE KEY)",
    "destructive_command": r"(rm -rf|shred |chmod \+x|curl |wget |nc -e|ncat -e|powershell -enc)",
}

RISKY_PICKLE_MARKERS: tuple[bytes, ...] = (
    b"cos\nsystem\n",
    b"posix\nsystem\n",
    b"nt\nsystem\n",
    b"subprocess\n",
    b"os\nsystem\n",
    b"builtins\neval\n",
    b"builtins\nexec\n",
    b"GLOBAL",
    b"REDUCE",
)

PYTHON_DANGEROUS_CALLS: frozenset[tuple[str, str]] = frozenset(
    {
        ("builtins", "eval"),
        ("builtins", "exec"),
        ("builtins", "compile"),
        ("marshal", "loads"),
        ("os", "popen"),
        ("os", "remove"),
        ("os", "system"),
        ("pickle", "load"),
        ("pickle", "loads"),
        ("shutil", "rmtree"),
        ("subprocess", "Popen"),
        ("subprocess", "call"),
        ("subprocess", "check_call"),
        ("subprocess", "check_output"),
        ("subprocess", "run"),
    }
)
