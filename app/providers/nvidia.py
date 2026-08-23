import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition


class NvidiaProvider(BaseProvider):
    FREE_MODELS = [
        {"id": "meta/llama-3.3-70b-instruct", "name": "Llama 3.3 70B"},
        {"id": "nvidia/llama-3.1-nemotron-70b-instruct", "name": "Nemotron 70B"},
        {"id": "mistralai/mistral-nemo-12b-instruct", "name": "Mistral NeMo 12B"},
        {"id": "microsoft/phi-3.5-mini-instruct", "name": "Phi-3.5 Mini"},
        {"id": "google/gemma-2-9b-it", "name": "Gemma 2 9B"},
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
            "messages": [{"role": m.role, "content": m.content} for m in messages],
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

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            yield resp.json()

    def list_models(self) -> list[dict]:
        return self.FREE_MODELS
