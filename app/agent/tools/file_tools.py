import os
import json
from pathlib import Path
import aiofiles


async def create_file(path: str, content: str) -> str:
    """Create or overwrite a file with the given content."""
    full_path = Path(path).resolve()
    full_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(full_path, "w") as f:
        await f.write(content)
    return json.dumps({"status": "created", "path": str(full_path), "size": len(content)})


async def read_file(path: str) -> str:
    """Read and return the contents of a file."""
    full_path = Path(path).resolve()
    if not full_path.exists():
        return json.dumps({"error": f"File not found: {path}"})
    async with aiofiles.open(full_path, "r", errors="replace") as f:
        content = await f.read()
    if len(content) > 100_000:
        content = content[:100_000] + "\n... (truncated)"
    return json.dumps({"path": str(full_path), "content": content})


async def list_directory(path: str = ".") -> str:
    """List files and directories at the given path."""
    full_path = Path(path).resolve()
    if not full_path.is_dir():
        return json.dumps({"error": f"Not a directory: {path}"})
    entries = []
    for entry in sorted(full_path.iterdir()):
        entries.append({
            "name": entry.name,
            "type": "dir" if entry.is_dir() else "file",
            "size": entry.stat().st_size if entry.is_file() else None,
        })
    return json.dumps({"path": str(full_path), "entries": entries})


async def delete_file(path: str) -> str:
    """Delete a file."""
    full_path = Path(path).resolve()
    if full_path.is_file():
        full_path.unlink()
        return json.dumps({"status": "deleted", "path": str(full_path)})
    return json.dumps({"error": f"Not a file: {path}"})


async def append_file(path: str, content: str) -> str:
    """Append content to an existing file."""
    full_path = Path(path).resolve()
    full_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(full_path, "a") as f:
        await f.write(content)
    return json.dumps({"status": "appended", "path": str(full_path)})


FILE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create or overwrite a file with content. Creates parent directories automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories at a path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: current)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "Append content to an existing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to append"},
                },
                "required": ["path", "content"],
            },
        },
    },
]
