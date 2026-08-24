# ⚡ Nexus AI

A hybrid native/web AI agent with tool use, advanced search, file creation, and command execution.

## Features

- **Multi-Provider LLM Support** — OpenRouter (free models), NVIDIA NIM, OpenCode Zen
- **Agent Loop** — Iterative reasoning with automatic tool calling
- **Installable App** — PWA/standalone mode on Android, desktop, iOS, and iPadOS
- **File Operations** — Workspace-sandboxed create, read, append, delete, binary, copy, and move tools
- **Advanced Web Search** — DuckDuckGo search + URL fetching
- **Powerful Runtime** — Shell commands, compilers, Node.js/npm, Git, ripgrep, SQLite, archives, and process-group timeouts
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

If an older command stays on `Waiting...`, paste this bounded recovery command instead:

```bash
for i in $(seq 1 24); do pgrep -x apt >/dev/null || pgrep -x apt-get >/dev/null || pgrep -x dpkg >/dev/null || break; sleep 5; done; if pgrep -x apt >/dev/null || pgrep -x apt-get >/dev/null || pgrep -x dpkg >/dev/null; then pgrep -ax apt; pgrep -ax apt-get; pgrep -ax dpkg; echo 'Close all other Termux sessions, force-stop Termux, reopen it, and retry.'; else rm -f $PREFIX/var/lib/dpkg/lock-frontend $PREFIX/var/lib/dpkg/lock $PREFIX/var/lib/apt/lists/lock $PREFIX/var/cache/apt/archives/lock; dpkg --configure -a; pkg update -y && bash <(curl -L https://raw.githubusercontent.com/LorEnzzhhz/nexus-ai/main/install.sh); fi
```

Then run `./start.sh` and open `http://localhost:8000` in your browser.

For a native-app experience, open the URL in Chrome or Firefox and choose **Add to Home screen / Install**.

## Android App (APK)

The repository includes a real Android app that wraps the running backend in a WebView:

- Source: `android/NexusApp/` (Android Studio project)
- Build: open `android/NexusApp` in Android Studio, connect your phone, and **Run** (or generate a signed APK).
- On a physical device the WebView loads `http://localhost:8000`, so start the backend first with `./start.sh` (or the `nexus` Termux launcher). In the emulator use `http://10.0.2.2:8000`.
- The backend must be running on the same device (Termux) for the app to work.

Quick flow on Android:
1. In Termux: `bash <(curl -L https://raw.githubusercontent.com/LorEnzzhhz/nexus-ai/main/install.sh)`
2. Run `nexus` (or `bash ~/nexus-ai/nexus-launch.sh`) to start the server and open the UI.
3. Build/install `android/NexusApp` from Android Studio for a home-screen app icon.

For a browser-based install instead, open `http://localhost:8000` in Chrome and choose **Add to Home screen**.

## API Keys

| Provider | Get Key | Free Models |
|----------|---------|-------------|
| OpenRouter | [openrouter.ai](https://openrouter.ai) | Llama 3.3, Gemini, DeepSeek, Mistral, Qwen |
| NVIDIA NIM | [build.nvidia.com](https://build.nvidia.com) | Nemotron, Llama 3.3, Phi-3.5, Gemma |
| OpenCode Zen | [opencode.ai/zen](https://opencode.ai/zen) | Nemotron, Big Pickle, MiMo, Hy3, Muse Spark, Laguna |

## Architecture

```
nexus-ai/
├── app/
│   ├── main.py              # Starlette/uvicorn entry point
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
├── static/                   # Installable PWA frontend
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
