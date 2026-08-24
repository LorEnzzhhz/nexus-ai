import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition, serialize_messages


class OpenCodeZenProvider(BaseProvider):
    FREE_MODELS = [
        {"id": "nemotron-3-ultra-free", "name": "Nemotron 3 Ultra (Free)"},
        {"id": "nemotron-3.5-lightning-free", "name": "Nemotron 3.5 Lightning (Free)"},
        {"id": "big-pickle", "name": "Big Pickle (Free Stealth)"},
        {"id": "x-preview-f-free", "name": "Ox Alpha (Free Stealth)"},
        {"id": "mimo-v2.5-free", "name": "MiMo-V2.5 (Free)"},
        {"id": "hy3-free", "name": "Hy3 (Free)"},
        {"id": "muse-spark-1.2-contributor-free", "name": "Muse Spark 1.2 Contributor (Free)"},
        {"id": "laguna-s-2.1-free", "name": "Laguna S 2.1 (Free)"},
    ]

    async def chat(
        self,
        model: str,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> AsyncIterator[dict]:
        payload: dict = {
            "model": model,
            "messages": serialize_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            yield resp.json()

    def list_models(self) -> list[dict]:
        return self.FREE_MODELS

    async def fetch_live_models(self) -> list[dict]:
        models = await super().fetch_live_models()
        live_free = [model for model in models if str(model.get("id", "")).endswith("-free")]
        known_free = next((model for model in models if model.get("id") == "big-pickle"), None)
        if known_free:
            live_free.append({"id": known_free["id"], "name": "Big Pickle (Free Stealth)"})
        return live_free or self.FREE_MODELS
