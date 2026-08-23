import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition


class OpenRouterProvider(BaseProvider):
    FREE_MODELS = [
        {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (Free)"},
        {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash (Free)"},
        {"id": "deepseek/deepseek-chat:free", "name": "DeepSeek Chat (Free)"},
        {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B (Free)"},
        {"id": "qwen/qwen-2.5-72b-instruct:free", "name": "Qwen 2.5 72B (Free)"},
        {"id": "microsoft/phi-3-medium-128k-instruct:free", "name": "Phi-3 Medium (Free)"},
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
