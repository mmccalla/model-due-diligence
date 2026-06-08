"""Default constants for model-due-diligence.

Keep this module free of runtime logic. It should contain shared configuration
values only, so scanners, external adapters and reporting code use one
consistent source of defaults.
"""

from __future__ import annotations

APP_NAME = "model-due-diligence"
CLI_SHORT_NAME = "mdd"
PACKAGE_NAME = "model_due_diligence"

DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_FAIL_ON = "HIGH"
DEFAULT_OUTPUT_DIRECTORY = "./model-audit-report"

MAX_TEXT_SCAN_BYTES = 2_000_000
MAX_BINARY_STRING_SCAN_BYTES = 50_000_000
BINARY_STRING_MIN_LENGTH = 6
SAFETENSORS_MAX_HEADER_BYTES = 100 * 1024 * 1024
GGUF_MAGIC = b"GGUF"

HIGH_RISK_SERIALISATION_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".bin",
        ".ckpt",
        ".h5",
        ".hdf5",
        ".joblib",
        ".mar",
        ".pb",
        ".pickle",
        ".pkl",
        ".pt",
        ".pth",
    }
)

LOWER_RISK_MODEL_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".gguf",
        ".onnx",
        ".safetensors",
    }
)

MODEL_EXTENSIONS: frozenset[str] = HIGH_RISK_SERIALISATION_EXTENSIONS | LOWER_RISK_MODEL_EXTENSIONS

EXECUTABLE_OR_SCRIPT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".bash",
        ".bat",
        ".cmd",
        ".dll",
        ".dylib",
        ".exe",
        ".fish",
        ".ps1",
        ".py",
        ".sh",
        ".so",
        ".zsh",
    }
)

COMPILED_BINARY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".dll",
        ".dylib",
        ".exe",
        ".so",
    }
)

TEXT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".bash",
        ".bat",
        ".cfg",
        ".cmd",
        ".dockerfile",
        ".env",
        ".fish",
        ".ini",
        ".json",
        ".md",
        ".modelfile",
        ".ps1",
        ".py",
        ".requirements",
        ".sh",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
        ".zsh",
    }
)

KNOWN_TEXT_FILENAMES: frozenset[str] = frozenset(
    {
        ".dockerignore",
        ".env.example",
        ".gitattributes",
        ".gitignore",
        ".python-version",
        "dockerfile",
        "licence",
        "license",
        "modelfile",
        "pdm.lock",
        "poetry.lock",
        "pyproject.toml",
        "readme.md",
        "requirements-dev.txt",
        "requirements-scanners.txt",
        "requirements.txt",
        "setup.cfg",
        "setup.py",
        "uv.lock",
        "environment.yaml",
        "environment.yml",
    }
)

DEPENDENCY_FILE_NAMES: frozenset[str] = frozenset(
    {
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-scanners.txt",
        "pyproject.toml",
        "poetry.lock",
        "pdm.lock",
        "uv.lock",
        "environment.yml",
        "environment.yaml",
    }
)

REPORT_MARKDOWN_FILENAME = "model_due_diligence_report.md"
REPORT_JSON_FILENAME = "model_due_diligence_report.json"
REPORT_SARIF_FILENAME = "model_due_diligence_report.sarif"

RAW_MODELSCAN_FILENAME = "modelscan.json"
RAW_SEMGREP_FILENAME = "semgrep.json"
RAW_BANDIT_FILENAME = "bandit.json"
RAW_DETECT_SECRETS_FILENAME = "detect-secrets.json"

SUPPORTED_REPORT_FORMATS: frozenset[str] = frozenset({"markdown", "json", "sarif"})

DEFAULT_IGNORED_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "audit-smoke",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
    }
)
