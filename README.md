# ⚡ Nexus AI

A powerful multi-provider AI agent with tool use, web search, file creation, and shell execution.

## Features

- **Multi-Provider LLM Support** — OpenRouter (free models), NVIDIA NIM, OpenCode Zen
- **Agent Loop** — Iterative reasoning with automatic tool calling
- **File Operations** — Create, read, append, delete files in workspace
- **Advanced Web Search** — DuckDuckGo search + URL fetching
- **Shell Execution** — Run any command in the container
- **Modern Web UI** — Dark-themed chat interface with activity panel and file explorer

## Quick Start

### Local Development

```bash
cd nexus-ai
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

Open http://localhost:8000

### Docker

```bash
docker compose up --build
```

### Termux (Android)

Paste this one-liner in Termux:

```bash
bash <(curl -L https://raw.githubusercontent.com/LorEnzzhhz/nexus-ai/main/install.sh)
```

If Termux reports that another `apt` or `dpkg` process is running, leave that process running. The installer waits automatically when Python still needs to be installed.

Then run `./start.sh` and open `http://localhost:8000` in your browser.

## API Keys

| Provider | Get Key | Free Models |
|----------|---------|-------------|
| OpenRouter | [openrouter.ai](https://openrouter.ai) | Llama 3.3, Gemini, DeepSeek, Mistral, Qwen |
| NVIDIA NIM | [build.nvidia.com](https://build.nvidia.com) | Nemotron, Llama 3.3, Phi-3.5, Gemma |
| OpenCode Zen | Set `OPENCODE_ZEN_BASE_URL` to your endpoint |

## Architecture

```
nexus-ai/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Configuration
│   ├── providers/            # LLM providers
│   │   ├── base.py           # Provider interface
│   │   ├── openrouter.py     # OpenRouter free models
│   │   ├── nvidia.py         # NVIDIA NIM models
│   │   └── opencode_zen.py   # OpenCode Zen
│   ├── agent/
│   │   ├── core.py           # Agent loop + orchestration
│   │   └── tools/
│   │       ├── file_tools.py # File CRUD operations
│   │       ├── search_tools.py # Web search + URL fetch
│   │       └── shell_tools.py  # Shell command execution
│   └── api/routes.py         # API endpoints
├── static/                   # Frontend (HTML/CSS/JS)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
