#!/data/data/com.termux/files/usr/bin/bash
set -e

clear
echo ""
echo "  ⚡ NEXUS AI INSTALLER"
echo "  ────────────────────"

wait_for_package_manager() {
    waited=0
    while pgrep -x apt >/dev/null 2>&1 || pgrep -x apt-get >/dev/null 2>&1 || pgrep -x dpkg >/dev/null 2>&1; do
        if (( waited == 0 )); then
            echo "[*] Waiting up to 2 minutes for Termux package manager..."
        fi
        sleep 5
        waited=$((waited + 5))
        if (( waited >= 120 )); then
            echo "[!] apt/dpkg is still active after 2 minutes." >&2
            pgrep -ax apt || true
            pgrep -ax apt-get || true
            pgrep -ax dpkg || true
            echo "[!] Close every other Termux session, force-stop Termux, reopen it, then run the recovery command." >&2
            exit 1
        fi
    done
}

repair_package_manager() {
    wait_for_package_manager
    echo "[*] Repairing Termux package state..."
    rm -f "$PREFIX/var/lib/dpkg/lock-frontend" "$PREFIX/var/lib/dpkg/lock" "$PREFIX/var/lib/apt/lists/lock" "$PREFIX/var/cache/apt/archives/lock"
    dpkg --configure -a
}

if ! command -v python3 >/dev/null 2>&1; then
    echo "[*] Installing Python..."
    repair_package_manager
    pkg install -y python
fi

if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "[*] Installing pip..."
    repair_package_manager
    pkg install -y python-pip
fi

echo "[*] Installing packages..."
echo "[*] Installing Python packages..."
python3 -m pip install --quiet --break-system-packages fastapi uvicorn httpx beautifulsoup4 aiofiles

mkdir -p workspace static app/providers app/agent/tools app/api
touch app/__init__.py app/providers/__init__.py app/agent/__init__.py app/agent/tools/__init__.py app/api/__init__.py

# Create config.py
cat > app/config.py << 'PYEOF'
import os
from pathlib import Path
class Config:
    APP_NAME = "Nexus AI"
    VERSION = "1.0.0"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", "./workspace"))
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
    OPENCODE_ZEN_API_KEY = os.getenv("OPENCODE_ZEN_API_KEY", "")
    OPENCODE_ZEN_BASE_URL = os.getenv("OPENCODE_ZEN_BASE_URL", "https://opencode.ai/zen/v1")
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openrouter")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
    MAX_ITERATIONS = 15
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7
PYEOF

# Create base provider
cat > app/providers/base.py << 'PYEOF'
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator
@dataclass
class Message:
    role: str
    content: str
@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
class BaseProvider(ABC):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    @abstractmethod
    async def chat(self, model: str, messages: list[Message], tools: list[ToolDefinition] | None = None, temperature: float = 0.7, max_tokens: int = 4096) -> AsyncIterator[dict]:
        ...
    @abstractmethod
    def list_models(self) -> list[dict]:
        ...
PYEOF

# Create OpenRouter provider
cat > app/providers/openrouter.py << 'PYEOF'
import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition


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
PYEOF

# Create NVIDIA provider
cat > app/providers/nvidia.py << 'PYEOF'
import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition


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
PYEOF

# Create OpenCode Zen provider
cat > app/providers/opencode_zen.py << 'PYEOF'
import httpx
from typing import AsyncIterator
from .base import BaseProvider, Message, ToolDefinition


class OpenCodeZenProvider(BaseProvider):
    FREE_MODELS = [
        {"id": "nemotron-3-ultra-free", "name": "Nemotron 3 Ultra (Free)"},
        {"id": "nemotron-3.5-lightning-free", "name": "Nemotron 3.5 Lightning (Free)"},
        {"id": "big-pickle", "name": "Big Pickle (Free Stealth)"},
        {"id": "x-preview-f-free", "name": "Ox Alpha (Free Stealth)"},
        {"id": "mimo-v2.5-free", "name": "MiMo-V2.5 (Free)"},
        {"id": "hy3-free", "name": "Hy3 (Free)"},
        {"id": "muse-spark-1.2-contributor-free", "name": "Muse Spark 1.2 Contributor (Free)"},
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
PYEOF

# Create providers __init__
cat > app/providers/__init__.py << 'PYEOF'
def get_provider(name):
    from ..config import Config
    providers = {
        "openrouter": lambda: __import__('app.providers.openrouter', fromlist=['OpenRouterProvider']).OpenRouterProvider(Config.OPENROUTER_API_KEY, Config.OPENROUTER_BASE_URL),
        "nvidia": lambda: __import__('app.providers.nvidia', fromlist=['NvidiaProvider']).NvidiaProvider(Config.NVIDIA_API_KEY, Config.NVIDIA_BASE_URL),
        "opencode_zen": lambda: __import__('app.providers.opencode_zen', fromlist=['OpenCodeZenProvider']).OpenCodeZenProvider(Config.OPENCODE_ZEN_API_KEY, Config.OPENCODE_ZEN_BASE_URL),
    }
    factory = providers.get(name)
    return factory() if factory else None
PYEOF

# Create file tools
cat > app/agent/tools/file_tools.py << 'PYEOF'
import json, base64
from pathlib import Path
import aiofiles
async def create_file(path, content):
    p = Path(path).resolve(); p.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(p, "w") as f: await f.write(content)
    return json.dumps({"status": "created", "path": str(p)})
async def read_file(path):
    p = Path(path).resolve()
    async with aiofiles.open(p, "r", errors="replace") as f: content = await f.read()
    return json.dumps({"path": str(p), "content": content[:50000]})
async def list_directory(path="."):
    p = Path(path).resolve()
    entries = [{"name": e.name, "type": "dir" if e.is_dir() else "file"} for e in sorted(p.iterdir())]
    return json.dumps({"entries": entries})
async def delete_file(path):
    Path(path).resolve().unlink(missing_ok=True)
    return json.dumps({"status": "deleted"})
async def append_file(path, content):
    p = Path(path).resolve(); p.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(p, "a") as f: await f.write(content)
    return json.dumps({"status": "appended"})
async def write_binary_file(path, content_base64):
    p = Path(path).resolve(); p.parent.mkdir(parents=True, exist_ok=True)
    data = base64.b64decode(content_base64)
    async with aiofiles.open(p, "wb") as f: await f.write(data)
    return json.dumps({"status": "created"})
async def copy_file(source, destination):
    import shutil
    src, dst = Path(source).resolve(), Path(destination).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
    return json.dumps({"status": "copied"})
async def move_file(source, destination):
    import shutil
    shutil.move(source, destination)
    return json.dumps({"status": "moved"})
async def create_directory(path):
    Path(path).resolve().mkdir(parents=True, exist_ok=True)
    return json.dumps({"status": "created"})
FILE_TOOLS = [
    {"type":"function","function":{"name":"create_file","description":"Create any text file","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},
    {"type":"function","function":{"name":"read_file","description":"Read a file","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"list_directory","description":"List directory contents","parameters":{"type":"object","properties":{"path":{"type":"string"}}}}},
    {"type":"function","function":{"name":"delete_file","description":"Delete a file","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"append_file","description":"Append to file","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},
    {"type":"function","function":{"name":"write_binary_file","description":"Write binary file from base64","parameters":{"type":"object","properties":{"path":{"type":"string"},"content_base64":{"type":"string"}},"required":["path","content_base64"]}}},
    {"type":"function","function":{"name":"copy_file","description":"Copy file","parameters":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}}},
    {"type":"function","function":{"name":"move_file","description":"Move/rename file","parameters":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}}},
    {"type":"function","function":{"name":"create_directory","description":"Create directory","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
]
PYEOF

# Create search tools
cat > app/agent/tools/search_tools.py << 'PYEOF'
import httpx, json
from bs4 import BeautifulSoup
async def web_search(query, max_results=5):
    results = []
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get("https://html.duckduckgo.com/html/", params={"q": query}, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for r in soup.select(".result")[:max_results]:
            t = r.select_one(".result__title a")
            s = r.select_one(".result__snippet")
            if t:
                results.append({"title": t.get_text(strip=True), "url": t.get("href",""), "snippet": s.get_text(strip=True) if s else ""})
    except Exception as e:
        return json.dumps({"error": str(e)})
    return json.dumps({"results": results})
async def fetch_url(url):
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script","style"]): tag.decompose()
        return json.dumps({"url": url, "content": soup.get_text(separator="\n", strip=True)[:30000]})
    except Exception as e:
        return json.dumps({"error": str(e)})
SEARCH_TOOLS = [
    {"type":"function","function":{"name":"web_search","description":"Search the web","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
    {"type":"function","function":{"name":"fetch_url","description":"Fetch URL content","parameters":{"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}}},
]
PYEOF

# Create shell tools
cat > app/agent/tools/shell_tools.py << 'PYEOF'
import asyncio, json, os
from pathlib import Path
async def run_command(command, timeout=60):
    cwd = str(Path("./workspace").resolve())
    Path(cwd).mkdir(exist_ok=True)
    try:
        proc = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd)
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return json.dumps({"exit_code": proc.returncode, "stdout": stdout.decode()[:20000], "stderr": stderr.decode()[:10000]})
    except asyncio.TimeoutError:
        return json.dumps({"error": "timeout"})
SHELL_TOOLS = [{"type":"function","function":{"name":"run_command","description":"Run shell command","parameters":{"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}}}]
PYEOF

cat > app/agent/tools/__init__.py << 'PYEOF'
import json
from .file_tools import FILE_TOOLS, create_file, read_file, list_directory, delete_file, append_file, write_binary_file, copy_file, move_file, create_directory
from .search_tools import SEARCH_TOOLS, web_search, fetch_url
from .shell_tools import SHELL_TOOLS, run_command

ALL_TOOLS = FILE_TOOLS + SEARCH_TOOLS + SHELL_TOOLS
TOOL_REGISTRY = {
    "create_file": create_file, "read_file": read_file, "list_directory": list_directory,
    "delete_file": delete_file, "append_file": append_file, "write_binary_file": write_binary_file,
    "copy_file": copy_file, "move_file": move_file, "create_directory": create_directory,
    "web_search": web_search, "fetch_url": fetch_url, "run_command": run_command,
}
async def execute_tool(name, args):
    func = TOOL_REGISTRY.get(name)
    if not func: return json.dumps({"error": f"Unknown tool: {name}"})
    try: return await func(**args)
    except Exception as e: return json.dumps({"error": str(e)})
PYEOF

# Create agent core
cat > app/agent/core.py << 'PYEOF'
import json
from ..providers.base import Message, ToolDefinition
from ..providers import get_provider
from .tools import ALL_TOOLS, execute_tool
from ..config import Config

SYSTEM_PROMPT = """You are Nexus AI, an autonomous agent with full tool access.
You can create files, search the web, run shell commands, and build anything.
When asked to build something, actually create the files and verify they work."""

class AgentCore:
    def _build_tool_defs(self):
        return [ToolDefinition(name=t["function"]["name"], description=t["function"]["description"], parameters=t["function"]["parameters"]) for t in ALL_TOOLS]

    async def run(self, session_id, user_message, provider_name="openrouter", model=None):
        provider = get_provider(provider_name)
        if not model: model = Config.DEFAULT_MODEL
        tool_defs = self._build_tool_defs()
        messages_for_llm = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}]

        for iteration in range(Config.MAX_ITERATIONS):
            response_content = ""
            tool_calls = []
            finish_reason = ""
            async for chunk in provider.chat(model=model, messages=[Message(role=m["role"], content=m["content"]) for m in messages_for_llm], tools=tool_defs, temperature=Config.TEMPERATURE, max_tokens=Config.MAX_TOKENS):
                choice = chunk.get("choices",[{}])[0]
                msg = choice.get("message",{})
                if msg.get("content"): response_content += msg["content"]
                if msg.get("tool_calls"): tool_calls = msg["tool_calls"]
                finish_reason = choice.get("finish_reason","")

            if not tool_calls: break

            assistant_msg = {"role": "assistant", "content": response_content}
            assistant_msg["tool_calls"] = [{"id": tc.get("id",f"c{iteration}_{i}"), "type": "function", "function": tc["function"]} for i, tc in enumerate(tool_calls)]
            messages_for_llm.append(assistant_msg)

            yield json.dumps({"type": "tool_calls", "tools": [tc["function"]["name"] for tc in tool_calls]}) + "\n"

            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except: args = {}
                result = await execute_tool(fn_name, args)
                yield json.dumps({"type": "tool_result", "tool": fn_name, "result": result[:500]}) + "\n"
                messages_for_llm.append({"role": "tool", "tool_call_id": tc.get("id",""), "content": result[:4000]})

        yield json.dumps({"type": "final", "content": response_content or "Done."}) + "\n"
PYEOF

cat > app/agent/__init__.py << 'PYEOF'
PYEOF

# Create API routes
cat > app/api/routes.py << 'PYEOF'
import json, uuid
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ..agent.core import AgentCore
from ..providers import get_provider
from ..config import Config
router = APIRouter()
agent = AgentCore()

@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    session_id = body.get("session_id", str(uuid.uuid4()))
    message = body.get("message", "")
    provider_name = body.get("provider", Config.DEFAULT_PROVIDER)
    model = body.get("model")
    async def generate():
        async for chunk in agent.run(session_id, message, provider_name, model):
            yield chunk
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/providers")
async def list_providers():
    info = []
    for name in ["openrouter", "nvidia", "opencode_zen"]:
        try:
            p = get_provider(name)
            if p:
                info.append({"id": name, "models": p.list_models(), "configured": bool(p.api_key)})
        except: pass
    return {"providers": info}

@router.get("/files")
async def list_files(path: str = "."):
    from ..agent.tools import execute_tool
    result = await execute_tool("list_directory", {"path": path})
    return json.loads(result)

@router.get("/health")
async def health():
    return {"status": "ok"}
PYEOF

cat > app/api/__init__.py << 'PYEOF'
PYEOF

# Create main.py
cat > app/main.py << 'PYEOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from .api.routes import router
app = FastAPI(title="Nexus AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "app": "Nexus AI"})
PYEOF

cat > app/__init__.py << 'PYEOF'
PYEOF

# Create frontend
cat > static/index.html << 'HTMLEOF'
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexus AI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:monospace;background:#0d1117;color:#e6edf3;height:100vh;display:flex;flex-direction:column}
header{padding:12px 16px;border-bottom:1px solid #30363d;font-size:14px}
#chat{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:90%}
.msg.user{align-self:flex-end}.msg.user .bubble{background:#1a5276;border-radius:12px;padding:10px 14px;font-size:13px}
.msg.assistant{align-self:flex-start}.msg.assistant .bubble{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:10px 14px;font-size:13px;white-space:pre-wrap}
.tool{font-size:11px;color:#bc8cff;margin-top:6px;padding:4px 8px;background:rgba(188,140,255,.1);border-radius:8px}
#input-area{padding:12px 16px;border-top:1px solid #30363d;display:flex;gap:8px}
input{flex:1;padding:10px 14px;background:#161b22;color:#e6edf3;border:1px solid #30363d;border-radius:8px;font-size:14px;outline:none}
button{width:44px;height:44px;background:#58a6ff;color:white;border:none;border-radius:8px;cursor:pointer;font-size:16px}
select{padding:8px;background:#161b22;color:#e6edf3;border:1px solid #30363d;border-radius:6px;font-size:12px;margin-bottom:8px}
</style></head><body>
<header>⚡ Nexus AI<br><select id="provider"></select><select id="model"></select></header>
<div id="chat"></div>
<div id="input-area"><input id="input" placeholder="Ask anything..."><button onclick="send()">➤</button></div>
<script>
const chat=document.getElementById('chat'),inp=document.getElementById('input');
let sessionId=null;
async function loadProviders(){
 const r=await fetch('/api/providers');const d=await r.json();
 const ps=document.getElementById('provider');ps.innerHTML='';
 d.providers.forEach(p=>{const o=document.createElement('option');o.value=p.id;o.textContent=p.id+(p.configured?' ✓':' ⚠');ps.appendChild(o)});
 updateModels();
}
async function updateModels(){
 const pid=document.getElementById('provider').value;
 const r=await fetch('/api/providers');const d=await r.json();
 const p=d.providers.find(x=>x.id===pid);if(!p)return;
 const ms=document.getElementById('model');ms.innerHTML='';
 p.models.forEach(m=>{const o=document.createElement('option');o.value=m.id;o.textContent=m.name;ms.appendChild(o)});
}
document.getElementById('provider').addEventListener('change',updateModels);
function addMsg(role,content){
 const el=document.createElement('div');el.className='message '+role;
 const b=document.createElement('div');b.className='bubble';b.textContent=content;
 el.appendChild(b);chat.appendChild(el);chat.scrollTop=chat.scrollHeight;
}
function addTool(name){
 const el=document.createElement('div');el.className='tool';el.textContent='⚡ '+name;
 chat.lastChild&&chat.appendChild(el);chat.scrollTop=chat.scrollHeight;
}
inp.addEventListener('keydown',e=>{if(e.key==='Enter')send()});
async function send(){
 const msg=inp.value.trim();if(!msg)return;
 inp.value='';addMsg('user',msg);
 try{
  const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,message:message,provider:document.getElementById('provider').value,model:document.getElementById('model').value})});
  const reader=res.body.getReader();const dec=new TextDecoder();
  let buffer='';
  while(true){
   const{done,value}=await reader.read();if(done)break;
   buffer+=dec.decode(value,{stream:true});
   const lines=buffer.split('\n');buffer=lines.pop();
   for(const line of lines){
    if(!line.trim())continue;
    try{
     const ev=JSON.parse(line);
     if(ev.type==='tool_calls')ev.tools.forEach(t=>addTool(t));
     if(ev.type==='final'){addMsg('assistant',ev.content);}
    }catch{}
   }
  }
 }catch(e){addMsg('assistant','Error: '+e.message)}
}
loadProviders();
</script>
</body></html>
HTMLEOF

touch static/style.css static/app.js

# Ask for keys
echo ""
read -r -p "OpenRouter key: " ORK || true
if [ -n "$ORK" ]; then export OPENROUTER_API_KEY="$ORK"; fi

read -r -p "NVIDIA key: " NVK || true
if [ -n "$NVK" ]; then export NVIDIA_API_KEY="$NVK"; fi

read -r -p "OpenCode Zen key: " OCZ || true
if [ -n "$OCZ" ]; then export OPENCODE_ZEN_API_KEY="$OCZ"; fi

# Save env
cat > .env << ENVF
OPENROUTER_API_KEY=${ORK:-}
NVIDIA_API_KEY=${NVK:-}
OPENCODE_ZEN_API_KEY=${OCZ:-}
OPENCODE_ZEN_BASE_URL=https://opencode.ai/zen/v1
ENVF

cat > start.sh << STARTEOF
#!/data/data/com.termux/files/usr/bin/bash
cd "\$(dirname "\$0")"
if [ -f .env ]; then
  set -a
  eval "\$(grep -v '^#' .env | grep -v '^\$')"
  set +a
fi
PORT="\${PORT:-8000}"
LOCAL_IP=\$(ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print \$2}' | head -1)
clear
echo ""
echo "  ╔════════════════════════╗"
echo "  ║      ⚡ NEXUS AI        ║"
echo "  ╠════════════════════════╣"
echo "  ║                        ║"
echo "  ║  http://localhost:\$PORT  ║"
[ -n "\$LOCAL_IP" ] && echo "  http://\${LOCAL_IP}:\${PORT}"
echo "  ║                        ║"
echo "  ║  Ctrl+C to stop        ║"
echo "  ╚════════════════════════╝"
echo ""
python3 -m uvicorn app.main:app --host 0.0.0.0 --port "\$PORT"
STARTEOF
chmod +x start.sh

echo ""
echo "  ✅ Setup complete!"
echo ""
echo "  Type: ./start.sh"
echo ""
