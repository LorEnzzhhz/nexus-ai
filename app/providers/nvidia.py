import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition, serialize_messages


class NvidiaProvider(BaseProvider):
    FREE_MODELS = [
        # NVIDIA Nemotron family
        {"id": "nvidia/nemotron-3-ultra-550b-a55b", "name": "Nemotron 3 Ultra 550B"},
        {"id": "nvidia/nemotron-3.5-lightning-30b-a3b", "name": "Nemotron 3.5 Lightning"},
        {"id": "nvidia/nemotron-3-super-120b-a12b", "name": "Nemotron 3 Super 120B"},
        {"id": "nvidia/nemotron-3-nano-30b-a3b", "name": "Nemotron Nano 30B A3B"},
        {"id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "name": "Nemotron Omni Reasoning"},
        {"id": "nvidia/nemotron-nano-3-30b-a3b", "name": "Nemotron Nano 3"},
        {"id": "nvidia/nemotron-nano-12b-v2-vl", "name": "Nemotron Nano 12B VL"},
        {"id": "nvidia/nvidia-nemotron-nano-9b-v2", "name": "Nemotron Nano 9B V2"},
        {"id": "nvidia/nemotron-4-340b-instruct", "name": "Nemotron 4 340B"},
        {"id": "nvidia/nemotron-mini-4b-instruct", "name": "Nemotron Mini 4B"},
        # Llama Nemotron
        {"id": "nvidia/llama-3.1-nemotron-ultra-253b-v1", "name": "Llama Nemotron Ultra 253B"},
        {"id": "nvidia/llama-3.3-nemotron-super-49b-v1.5", "name": "Llama Nemotron Super 49B v1.5"},
        {"id": "nvidia/llama-3.3-nemotron-super-49b-v1", "name": "Llama Nemotron Super 49B"},
        {"id": "nvidia/llama-3.1-nemotron-70b-instruct", "name": "Llama Nemotron 70B"},
        {"id": "nvidia/llama-3.1-nemotron-51b-instruct", "name": "Llama Nemotron 51B"},
        {"id": "nvidia/llama-3.1-nemotron-nano-8b-v1", "name": "Llama Nemotron Nano 8B"},
        {"id": "nvidia/llama-3.1-nemotron-nano-vl-8b-v1", "name": "Llama Nemotron Nano VL 8B"},
        # Meta Llama
        {"id": "meta/llama-3.3-70b-instruct", "name": "Llama 3.3 70B"},
        {"id": "meta/llama-3.1-70b-instruct", "name": "Llama 3.1 70B"},
        {"id": "meta/llama-3.1-8b-instruct", "name": "Llama 3.1 8B"},
        {"id": "meta/llama-3.2-90b-vision-instruct", "name": "Llama 3.2 90B Vision"},
        {"id": "meta/llama-3.2-11b-vision-instruct", "name": "Llama 3.2 11B Vision"},
        {"id": "meta/llama-3.2-3b-instruct", "name": "Llama 3.2 3B"},
        {"id": "meta/llama-3.2-1b-instruct", "name": "Llama 3.2 1B"},
        {"id": "meta/codellama-70b", "name": "CodeLlama 70B"},
        {"id": "meta/muse-glimmer-30b", "name": "Muse Glimmer 30B"},
        # OpenAI GPT-OSS
        {"id": "openai/gpt-oss-120b", "name": "GPT-OSS 120B"},
        {"id": "openai/gpt-oss-20b", "name": "GPT-OSS 20B"},
        # DeepSeek
        {"id": "deepseek-ai/deepseek-v4-flash-0731", "name": "DeepSeek V4 Flash"},
        {"id": "deepseek-ai/deepseek-coder-6.7b-instruct", "name": "DeepSeek Coder 6.7B"},
        # Mistral
        {"id": "mistralai/mistral-large-2-instruct", "name": "Mistral Large 2"},
        {"id": "mistralai/mistral-large", "name": "Mistral Large"},
        {"id": "mistralai/mistral-nemotron", "name": "Mistral Nemotron"},
        {"id": "mistralai/mixtral-8x22b-v0.1", "name": "Mixtral 8x22B"},
        {"id": "nv-mistralai/mistral-nemo-12b-instruct", "name": "Mistral NeMo 12B"},
        {"id": "mistralai/mistral-7b-instruct-v0.3", "name": "Mistral 7B v0.3"},
        {"id": "mistralai/codestral-22b-instruct-v0.1", "name": "Codestral 22B"},
        {"id": "nvidia/mistral-nemo-minitron-8b-8k-instruct", "name": "Mistral NeMo Minitron 8B"},
        # Google
        {"id": "google/gemma-4-31b-it", "name": "Gemma 4 31B"},
        {"id": "google/diffusiongemma-26b-a4b-it", "name": "Diffusion Gemma 26B"},
        {"id": "google/gemma-3-12b-it", "name": "Gemma 3 12B"},
        {"id": "google/gemma-3-4b-it", "name": "Gemma 3 4B"},
        {"id": "google/gemma-2b", "name": "Gemma 2B"},
        {"id": "google/codegemma-7b", "name": "CodeGemma 7B"},
        {"id": "google/codegemma-1.1-7b", "name": "CodeGemma 1.1 7B"},
        {"id": "google/recurrentgemma-2b", "name": "Recurrent Gemma 2B"},
        # Moonshot AI
        {"id": "moonshotai/kimi-k3", "name": "Kimi K3"},
        {"id": "moonshotai/kimi-k2.6", "name": "Kimi K2.6"},
        # Microsoft
        {"id": "microsoft/phi-3-vision-128k-instruct", "name": "Phi-3 Vision 128K"},
        {"id": "microsoft/phi-3.5-moe-instruct", "name": "Phi-3.5 MoE"},
        # Other providers
        {"id": "01-ai/yi-large", "name": "Yi Large"},
        {"id": "ai21labs/jamba-1.5-large-instruct", "name": "Jamba 1.5 Large"},
        {"id": "databricks/dbrx-instruct", "name": "DBRX Instruct"},
        {"id": "minimaxai/minimax-m3", "name": "MiniMax M3"},
        {"id": "stepfun-ai/step-3.7-flash", "name": "Step 3.7 Flash"},
        {"id": "thinkingmachines/inkling", "name": "Inkling"},
        {"id": "poolside/laguna-xs-2.1", "name": "Laguna XS 2.1"},
        {"id": "writer/palmyra-creative-122b", "name": "Palmyra Creative 122B"},
        {"id": "writer/palmyra-med-70b", "name": "Palmyra Med 70B"},
        {"id": "writer/palmyra-fin-70b-32k", "name": "Palmyra Fin 70B"},
        {"id": "zyphra/zamba2-7b-instruct", "name": "Zamba2 7B"},
        {"id": "aisingapore/sea-lion-7b-instruct", "name": "SEA-LION 7B"},
        {"id": "ibm/granite-3.0-8b-instruct", "name": "Granite 3.0 8B"},
        {"id": "bigcode/starcoder2-15b", "name": "StarCoder2 15B"},
        {"id": "adept/fuyu-8b", "name": "Fuyu 8B"},
        {"id": "nvidia/neva-22b", "name": "NeVA 22B"},
        {"id": "nvidia/vila", "name": "VILA"},
        {"id": "nvidia/cosmos-reason2-8b", "name": "Cosmos Reason 2 8B"},
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

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions", json=payload, headers=headers
            )
            resp.raise_for_status()
            yield resp.json()

    def list_models(self) -> list[dict]:
        return self.FREE_MODELS
