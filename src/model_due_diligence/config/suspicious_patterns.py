SUSPICIOUS_TEXT_PATTERNS: dict[str, str] = {
    "shell_execution": r"\b(os\.system|subprocess\.|popen\(|exec\(|eval\(|compile\()",
    "network_access": r"\b(requests\.|urllib\.|httpx\.|socket\.|ftplib\.|paramiko\.|scp\b|curl\b|wget\b|Invoke-WebRequest\b)",
    "destructive_file_ops": r"\b(rm\s+-rf|shutil\.rmtree|chmod\s+\+x|chown\b|unlink\(|remove\(|Delete-Item\b)",
    "secret_terms": r"\b(AWS_SECRET|AWS_ACCESS|OPENAI_API_KEY|HF_TOKEN|GITHUB_TOKEN|PRIVATE_KEY|BEGIN RSA|BEGIN OPENSSH|password|passwd|secret|token)",
    "obfuscation": r"\b(base64\.b64decode|fromhex\(|codecs\.decode|marshal\.loads|pickle\.loads|__import__\()",
    "environment_access": r"\b(os\.environ|getenv\(|printenv\b|env\s*\|)",
    "reverse_shell": r"\b(/bin/sh|/bin/bash|nc\s+-e|bash\s+-i|pty\.spawn|powershell\s+-enc)",
    "package_install": r"\b(pip\s+install|npm\s+install|curl\s+.*\|\s*(bash|sh)|wget\s+.*\|\s*(bash|sh))",
    "transformers_remote_code": r"trust_remote_code\s*=\s*True",
}

SUSPICIOUS_BINARY_STRINGS: dict[str, str] = {
    "url": r"https?://[^\s\"'<>]{8,}",
    "shell_path": r"/bin/(sh|bash|zsh)",
    "windows_shell": r"(powershell|cmd\.exe)",
    "env_var": r"(OPENAI_API_KEY|HF_TOKEN|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID)",
    "destructive_command": r"(rm -rf|chmod \+x|curl |wget |nc -e)",
}
