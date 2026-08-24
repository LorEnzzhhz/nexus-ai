import json
import uuid

from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route, Router

from ..agent.core import AgentCore, AgentSession
from ..providers import get_provider
from ..config import Config

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


router = Router(routes=[
    Route("/chat", chat, methods=["POST"]),
    Route("/providers", list_providers),
    Route("/sessions/{session_id}", get_session),
    Route("/files", list_files),
])
