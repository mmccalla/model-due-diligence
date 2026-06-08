APP_NAME = "model-due-diligence"
DEFAULT_TIMEOUT_SECONDS = 300
MAX_TEXT_SCAN_BYTES = 2_000_000
MAX_BINARY_STRING_SCAN_BYTES = 50_000_000
BINARY_STRING_MIN_LENGTH = 6
SAFETENSORS_MAX_HEADER_BYTES = 100 * 1024 * 1024
GGUF_MAGIC = b"GGUF"

HIGH_RISK_SERIALISATION_EXTENSIONS = {".pkl", ".pickle", ".pt", ".pth", ".bin", ".joblib", ".h5", ".hdf5", ".pb", ".ckpt", ".mar"}
LOWER_RISK_MODEL_EXTENSIONS = {".safetensors", ".gguf", ".onnx"}
MODEL_EXTENSIONS = HIGH_RISK_SERIALISATION_EXTENSIONS | LOWER_RISK_MODEL_EXTENSIONS
EXECUTABLE_OR_SCRIPT_EXTENSIONS = {".py", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd", ".exe", ".dll", ".so", ".dylib"}
TEXT_EXTENSIONS = {".py", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd", ".txt", ".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env", ".dockerfile", ".modelfile", ".requirements"}
KNOWN_TEXT_FILENAMES = {"dockerfile", "modelfile", "requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "poetry.lock", "pdm.lock", "uv.lock", "environment.yml", "environment.yaml", "readme.md", "license", "licence", ".gitattributes", ".gitignore"}
