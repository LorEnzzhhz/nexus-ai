import json
import uuid
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
    model = body.get("model", Config.DEFAULT_MODEL)

    if session_id not in agent.sessions:
        from ..agent.core import AgentSession
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


@router.get("/providers")
async def list_providers():
    providers_info = []
    for name in ["openrouter", "nvidia", "opencode_zen"]:
        try:
            p = get_provider(name)
            models = p.list_models()
            if p.api_key:
                try:
                    live = await p.fetch_live_models()
                    if live:
                        models = live
                except Exception:
                    pass
            providers_info.append({
                "id": name,
                "name": name.replace("_", " ").title(),
                "models": models,
                "configured": bool(p.api_key),
            })
        except Exception:
            pass
    return {"providers": providers_info}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    history = agent.get_session_history(session_id)
    return {"session_id": session_id, "messages": history}


@router.get("/files")
async def list_files(path: str = "."):
    result = await agent_sessions_list_dir(path)
    return json.loads(result)


async def agent_sessions_list_dir(path: str) -> str:
    from ..agent.tools import execute_tool
    return await execute_tool("list_directory", {"path": path})
