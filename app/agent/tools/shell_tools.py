import asyncio
import json
from pathlib import Path


def _get_cwd() -> str:
    from ...config import Config
    Config.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    return str(Config.WORKSPACE_DIR.resolve())


MAX_OUTPUT = 50_000


async def run_command(command: str, timeout: int = 60) -> str:
    """Execute a shell command and return stdout/stderr."""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=_get_cwd(),
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return json.dumps({"error": "Command timed out", "command": command})

        output = {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
        if len(output["stdout"]) > MAX_OUTPUT:
            output["stdout"] = output["stdout"][:MAX_OUTPUT] + "\n... (truncated)"
        if len(output["stderr"]) > MAX_OUTPUT // 2:
            output["stderr"] = output["stderr"][:MAX_OUTPUT // 2] + "\n... (truncated)"
        return json.dumps(output)
    except Exception as e:
        return json.dumps({"error": f"Execution failed: {e}", "command": command})


SHELL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command in the container environment. Can install packages, run scripts, compile code, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
                },
                "required": ["command"],
            },
        },
    },
]
