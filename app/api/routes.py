import json
import uuid

from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route, Router

from ..agent.core import AgentCore, AgentSession
from ..providers import get_provider
from ..config import Config
import pathlib
import re

ENV_PATH = pathlib.Path(".env")

agent = AgentCore()


async def chat(request: Request):
    body = await request.json()
    session_id = body.get("session_id", str(uuid.uuid4()))
    message = body.get("message", "")
    provider_name = body.get("provider", Config.DEFAULT_PROVIDER)
    model = body.get("model", Config.DEFAULT_MODEL)

    if session_id not in agent.sessions:
        agent.sessions[session_id] = AgentSession(provider_name=provider_name, model=model)
    else:
        agent.sessions[session_id].provider_name = provider_name
        agent.sessions[session_id].model = model

    async def generate():
        async for chunk in agent.run(session_id, message):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id},
    )


async def list_providers(request: Request):
    providers_info = []
    for name in ["openrouter", "nvidia", "opencode_zen"]:
        try:
            provider = get_provider(name)
            models = provider.list_models()
            if provider.api_key:
                try:
                    live = await provider.fetch_live_models()
                    if live:
                        models = live
                except Exception:
                    pass
            providers_info.append({
                "id": name,
                "name": name.replace("_", " ").title(),
                "models": models,
                "configured": bool(provider.api_key),
            })
        except Exception:
            pass
    return JSONResponse({"providers": providers_info})


async def get_session(request: Request):
    session_id = request.path_params["session_id"]
    return JSONResponse({
        "session_id": session_id,
        "messages": agent.get_session_history(session_id),
    })


async def list_files(request: Request):
    path = request.query_params.get("path", ".")
    result = await agent_sessions_list_dir(path)
    return JSONResponse(json.loads(result))


async def agent_sessions_list_dir(path: str) -> str:
    from ..agent.tools import execute_tool
    return await execute_tool("list_directory", {"path": path})


def _mask(value: str) -> str:
    value = value or ""
    if not value:
        return ""
    if len(value) <= 8:
        return "•" * len(value)
    return value[:4] + "•" * max(4, len(value) - 8) + value[-4:]


def _normalize_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


async def get_config(request: Request):
    return JSONResponse({
        "providers": {
            "openrouter": {"configured": bool(Config.OPENROUTER_API_KEY)},
            "nvidia": {"configured": bool(Config.NVIDIA_API_KEY)},
            "opencode_zen": {"configured": bool(Config.OPENCODE_ZEN_API_KEY)},
        },
        "defaults": {
            "provider": Config.DEFAULT_PROVIDER,
            "model": Config.DEFAULT_MODEL,
            "shell_enabled": Config.SHELL_ENABLED,
            "command_timeout": Config.COMMAND_TIMEOUT,
        },
        "keys": {
            "OPENROUTER_API_KEY": _mask(Config.OPENROUTER_API_KEY),
            "NVIDIA_API_KEY": _mask(Config.NVIDIA_API_KEY),
            "OPENCODE_ZEN_API_KEY": _mask(Config.OPENCODE_ZEN_API_KEY),
            "OPENCODE_ZEN_BASE_URL": Config.OPENCODE_ZEN_BASE_URL,
        },
    })


async def update_config(request: Request):
    data = await request.json()
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    for key in Config.RUNTIME_KEYS:
        if key not in data:
            continue
        raw = data[key]
        if raw is None:
            continue
        value = "true" if key == "SHELL_ENABLED" and _normalize_bool(raw) else str(raw)
        pattern = re.compile(rf"^{re.escape(key)}=")
        replacement = f"{key}={value}"
        if any(pattern.match(line) for line in lines):
            lines = [replacement if pattern.match(line) else line for line in lines]
        else:
            lines.append(replacement)
    ENV_PATH.write_text("\n".join(lines) + "\n")
    Config.update_runtime(data)
    return JSONResponse({"status": "ok"})


router = Router(routes=[
    Route("/chat", chat, methods=["POST"]),
    Route("/providers", list_providers),
    Route("/sessions/{session_id}", get_session),
    Route("/files", list_files),
    Route("/config", get_config),
    Route("/config", update_config, methods=["POST"]),
])
