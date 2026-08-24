import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition, serialize_messages


class OpenRouterProvider(BaseProvider):
    FREE_MODELS = [
        {"id": "nvidia/nemotron-3-ultra-550b-a55b:free", "name": "Nemotron 3 Ultra 550B"},
        {"id": "nvidia/nemotron-3.5-lightning:free", "name": "Nemotron 3.5 Lightning"},
        {"id": "nvidia/nemotron-3-super-120b-a12b:free", "name": "Nemotron 3 Super 120B"},
        {"id": "z-ai/glm-5.2:free", "name": "GLM 5.2"},
        {"id": "google/gemma-4-31b-it:free", "name": "Gemma 4 31B"},
        {"id": "google/gemma-4-26b-a4b-it:free", "name": "Gemma 4 26B A4B"},
        {"id": "thinkingmachines/inkling:free", "name": "Inkling"},
        {"id": "thinkingmachines/inkling-small:free", "name": "Inkling Small"},
        {"id": "cohere/north-mini-code:free", "name": "North Mini Code"},
        {"id": "dots-studio/dots-3-note-preview:free", "name": "Dots3 Note Preview"},
        {"id": "poolside/laguna-s-2.1:free", "name": "Laguna S 2.1"},
        {"id": "poolside/laguna-xs-2.1:free", "name": "Laguna XS 2.1"},
        {"id": "nvidia/nemotron-3-nano-30b-a3b:free", "name": "Nemotron Nano 30B A3B"},
        {"id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "name": "Nemotron Omni Reasoning"},
        {"id": "nvidia/nemotron-nano-12b-v2-vl:free", "name": "Nemotron Nano 12B VL"},
        {"id": "nvidia/nemotron-nano-9b-v2:free", "name": "Nemotron Nano 9B V2"},
        {"id": "liquid/lfm-2.5-2.6b:free", "name": "LFM 2.5 2.6B"},
        {"id": "nvidia/nemotron-3.5-content-safety:free", "name": "Nemotron Content Safety"},
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
            "stream": stream,
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
            "HTTP-Referer": "https://nexus-ai.local",
            "X-Title": "Nexus AI",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            if stream:
                async with client.stream(
                    "POST", f"{self.base_url}/chat/completions",
                    json=payload, headers=headers,
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            import json
                            yield json.loads(line[6:])
            else:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload, headers=headers,
                )
                resp.raise_for_status()
                yield resp.json()

    def list_models(self) -> list[dict]:
        return self.FREE_MODELS

    async def fetch_live_models(self) -> list[dict]:
        models = await super().fetch_live_models()
        live_free = [model for model in models if str(model.get("id", "")).endswith(":free")]
        return live_free or self.FREE_MODELS
