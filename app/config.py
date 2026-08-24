import os
from pathlib import Path


class Config:
    APP_NAME = "Nexus AI"
    VERSION = "1.1.0"

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "./workspace"))
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )

    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL = os.getenv(
        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
    )

    OPENCODE_ZEN_API_KEY = os.getenv("OPENCODE_ZEN_API_KEY", "")
    OPENCODE_ZEN_BASE_URL = os.getenv(
        "OPENCODE_ZEN_BASE_URL",
        "https://opencode.ai/zen/v1",
    )

    SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8888")

    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openrouter")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "15"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    SHELL_ENABLED = os.getenv("SHELL_ENABLED", "true").lower() in {"1", "true", "yes"}
    COMMAND_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "180"))
    MAX_COMMAND_OUTPUT = int(os.getenv("MAX_COMMAND_OUTPUT", "50000"))
    FILE_SIZE_LIMIT = int(os.getenv("FILE_SIZE_LIMIT", str(20 * 1024 * 1024)))

    ALLOWED_ORIGINS = ["*"]

    RUNTIME_KEYS = [
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "NVIDIA_API_KEY",
        "NVIDIA_BASE_URL",
        "OPENCODE_ZEN_API_KEY",
        "OPENCODE_ZEN_BASE_URL",
        "SEARXNG_URL",
        "DEFAULT_PROVIDER",
        "DEFAULT_MODEL",
        "MAX_ITERATIONS",
        "MAX_TOKENS",
        "TEMPERATURE",
        "SHELL_ENABLED",
        "COMMAND_TIMEOUT",
        "MAX_COMMAND_OUTPUT",
        "FILE_SIZE_LIMIT",
    ]

    @classmethod
    def update_runtime(cls, values: dict) -> None:
        for key, raw in values.items():
            if key not in cls.RUNTIME_KEYS or raw is None:
                continue
            value = raw
            if key in {"MAX_ITERATIONS", "MAX_TOKENS", "COMMAND_TIMEOUT", "MAX_COMMAND_OUTPUT", "FILE_SIZE_LIMIT"}:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    continue
            elif key in {"TEMPERATURE"}:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue
                cls.TEMPERATURE = value
                os.environ[key] = str(value)
                continue
            elif key == "SHELL_ENABLED":
                value = str(value).lower() in {"1", "true", "yes"}
                cls.SHELL_ENABLED = value
                os.environ[key] = str(value)
                continue
            setattr(cls, key, value)
            os.environ[key] = str(value)
