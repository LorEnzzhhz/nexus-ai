import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition


class OpenCodeZenProvider(BaseProvider):
    FREE_MODELS = [
        {"id": "deepseek/deepseek-chat-v3-0324", "name": "DeepSeek Chat V3"},
        {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1"},
        {"id": "qwen/qwen3-coder", "name": "Qwen3 Coder"},
        {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet 4"},
        {"id": "openai/gpt-4.1-mini", "name": "GPT-4.1 Mini"},
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
