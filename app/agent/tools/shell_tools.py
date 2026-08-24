import asyncio
import json
import os
import signal


SHELL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command in the isolated workspace/container runtime. Can create projects, install dependencies, run scripts, compile code, test applications, archive files, and inspect results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds; capped by COMMAND_TIMEOUT",
                    },
                },
                "required": ["command"],
            },
        },
    }
]


async def run_command(command: str, timeout: int | None = None) -> str:
    from ...config import Config

    if not Config.SHELL_ENABLED:
        return json.dumps({"error": "Shell execution is disabled by SHELL_ENABLED=false"})

    max_output = Config.MAX_COMMAND_OUTPUT
    effective_timeout = min(max(1, timeout or Config.COMMAND_TIMEOUT), Config.COMMAND_TIMEOUT)
    workspace = Config.WORKSPACE_DIR.resolve()
    tmp_dir = workspace / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(workspace),
            "TMPDIR": str(tmp_dir),
            "NEXUS_WORKSPACE": str(workspace),
            "TERM": environment.get("TERM", "dumb"),
        }
    )

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace,
            env=environment,
            start_new_session=True,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), effective_timeout)
        except asyncio.TimeoutError:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await process.communicate()
            return json.dumps(
                {
                    "error": "Command timed out",
                    "command": command,
                    "timeout_seconds": effective_timeout,
                }
            )

        output = {
            "command": command,
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
        if len(output["stdout"]) > max_output:
            output["stdout"] = output["stdout"][:max_output] + "\n... (truncated)"
        if len(output["stderr"]) > max_output // 2:
            output["stderr"] = output["stderr"][: max_output // 2] + "\n... (truncated)"
        return json.dumps(output)
    except Exception as exc:
        return json.dumps({"error": f"Execution failed: {exc}", "command": command})
