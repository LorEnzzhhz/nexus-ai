import json
import time
from dataclasses import dataclass, field
from typing import AsyncIterator

from ..providers.base import Message, ToolDefinition
from ..providers import get_provider
from .tools import ALL_TOOLS, execute_tool
from ..config import Config


SYSTEM_PROMPT = """You are Nexus AI, a powerful autonomous AI agent running in a full container environment.

You have access to tools:
- create_file / read_file / append_file / delete_file: manage files in the workspace
- list_directory: explore the filesystem
- web_search: search the internet for current information
- fetch_url: read content from any URL
- run_command: execute shell commands (install packages, compile, test, etc.)

You can create any type of file, write and run code in any language, install packages, and search the web. Use tools when needed to complete tasks fully.

When writing code or creating files, use best practices. When a task requires multiple steps, plan and execute them sequentially.

Always provide clear, helpful responses."""


@dataclass
class AgentSession:
    provider_name: str = "openrouter"
    model: str = ""
    messages: list[dict] = field(default_factory=list)
    max_iterations: int = Config.MAX_ITERATIONS


class AgentCore:
    def __init__(self):
        self.sessions: dict[str, AgentSession] = {}

    def _build_tool_defs(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name=t["function"]["name"],
                description=t["function"]["description"],
                parameters=t["function"]["parameters"],
            )
            for t in ALL_TOOLS
        ]

    async def run(self, session_id: str, user_message: str) -> AsyncIterator[str]:
        if session_id not in self.sessions:
            from ..config import Config
            self.sessions[session_id] = AgentSession(
                model=Config.DEFAULT_MODEL,
                max_iterations=Config.MAX_ITERATIONS,
            )

        session = self.sessions[session_id]
        session.messages.append({"role": "user", "content": user_message})

        provider = get_provider(session.provider_name)
        tool_defs = self._build_tool_defs()

        messages_for_llm = [{"role": "system", "content": SYSTEM_PROMPT}] + session.messages

        for iteration in range(session.max_iterations):
            response_content = ""
            tool_calls = []

            async for chunk in provider.chat(
                model=session.model,
                messages=[Message(role=m["role"], content=m["content"]) for m in messages_for_llm],
                tools=tool_defs,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
            ):
                choice = chunk.get("choices", [{}])[0]
                message = choice.get("message", {})
                if message.get("content"):
                    response_content += message["content"]
                if message.get("tool_calls"):
                    tool_calls = [
                        {
                            "id": tc.get("id", f"call_{iteration}_{i}"),
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            },
                        }
                        for i, tc in enumerate(message["tool_calls"])
                    ]
                finish_reason = choice.get("finish_reason", "")

            if tool_calls:
                assistant_msg = {"role": "assistant", "content": response_content}
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                messages_for_llm.append(assistant_msg)

                yield json.dumps({
                    "type": "tool_calls",
                    "tools": [{"name": tc["function"]["name"], "args": json.loads(tc["function"]["arguments"])} for tc in tool_calls],
                }) + "\n"

                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        args = {}

                    result = await execute_tool(fn_name, args)

                    yield json.dumps({
                        "type": "tool_result",
                        "tool": fn_name,
                        "result": result[:2000],
                    }) + "\n"

                    messages_for_llm.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result[:8000],
                    })

                continue

            break

        final_response = response_content or "Task completed."
        session.messages.append({"role": "assistant", "content": final_response})

        yield json.dumps({"type": "final", "content": final_response}) + "\n"

    def get_session_history(self, session_id: str) -> list[dict]:
        if session_id in self.sessions:
            return self.sessions[session_id].messages
        return []
