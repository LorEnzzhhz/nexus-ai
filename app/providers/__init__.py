from .base import BaseProvider, Message, ToolDefinition
from .openrouter import OpenRouterProvider
from .nvidia import NvidiaProvider
from .opencode_zen import OpenCodeZenProvider


def get_provider(name: str) -> BaseProvider:
    from ..config import Config

    providers = {
        "openrouter": lambda: OpenRouterProvider(
            Config.OPENROUTER_API_KEY, Config.OPENROUTER_BASE_URL
        ),
        "nvidia": lambda: NvidiaProvider(
            Config.NVIDIA_API_KEY, Config.NVIDIA_BASE_URL
        ),
        "opencode_zen": lambda: OpenCodeZenProvider(
            Config.OPENCODE_ZEN_API_KEY, Config.OPENCODE_ZEN_BASE_URL
        ),
    }
    factory = providers.get(name)
    if not factory:
        raise ValueError(f"Unknown provider: {name}")
    return factory()
