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
- create_file: create any text file (code, config, markdown, HTML, etc.)
- read_file: read any file's contents
- append_file: add content to an existing file
- delete_file: remove a file
- write_binary_file: create binary files (images, PDFs) from base64
- copy_file: copy files between paths
- move_file: move or rename files/directories
- list_directory: explore the filesystem
- create_directory: make directories with parents
- web_search: search the internet for current information
- fetch_url: read content from any URL
- run_command: execute commands inside the isolated workspace/container runtime

All file paths are rooted at the current workspace. You can create ANY type of file in ANY language. Write complete, production-quality code. Use tools proactively — don't just describe what to do, actually DO it. When asked to build something, create all necessary files, install dependencies, and verify it works by running it.

When creating projects:
1. Create a directory for the project
2. Write all source files with full implementations (no placeholders)
3. Install dependencies if needed
4. Run/test the code to verify it works

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
                messages=[
                    Message(
                        role=item["role"],
                        content=item.get("content", ""),
                        tool_calls=item.get("tool_calls"),
                        tool_call_id=item.get("tool_call_id"),
                    )
                    for item in messages_for_llm
                ],
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
                    "tools": [
                        {
                            "name": tc["function"]["name"],
                            "args": self._parse_arguments(tc["function"].get("arguments", "{}")),
                        }
                        for tc in tool_calls
                    ],
                }) + "\n"

                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    try:
                        args = self._parse_arguments(tc["function"].get("arguments", "{}"))
                    except (json.JSONDecodeError, TypeError):
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

    @staticmethod
    def _parse_arguments(value: object) -> dict:
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        return {}
