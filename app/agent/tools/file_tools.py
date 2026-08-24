import json
import base64
import shutil
from pathlib import Path
import aiofiles


def _resolve(path: str) -> Path:
    from ...config import Config

    workspace = Config.WORKSPACE_DIR.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    candidate = (workspace / path).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise ValueError("Path escapes the Nexus workspace") from exc
    return candidate


async def create_file(path: str, content: str) -> str:
    """Create or overwrite a file with the given content."""
    from ...config import Config

    full_path = _resolve(path)
    if len(content.encode()) > Config.FILE_SIZE_LIMIT:
        return json.dumps({"error": "File exceeds FILE_SIZE_LIMIT"})
    full_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(full_path, "w") as f:
        await f.write(content)
    return json.dumps({"status": "created", "path": str(full_path), "size": len(content)})


async def read_file(path: str) -> str:
    """Read and return the contents of a file."""
    full_path = _resolve(path)
    if not full_path.exists():
        return json.dumps({"error": f"File not found: {path}"})
    async with aiofiles.open(full_path, "r", errors="replace") as f:
        content = await f.read()
    if len(content) > 100_000:
        content = content[:100_000] + "\n... (truncated)"
    return json.dumps({"path": str(full_path), "content": content})


async def list_directory(path: str = ".") -> str:
    """List files and directories at the given path."""
    full_path = _resolve(path)
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
    """Delete a file or directory."""
    from ...config import Config

    full_path = _resolve(path)
    if full_path == Config.WORKSPACE_DIR.resolve():
        return json.dumps({"error": "Refusing to delete the workspace root"})
    if full_path.is_file():
        full_path.unlink()
        return json.dumps({"status": "deleted", "path": str(full_path)})
    if full_path.is_dir():
        shutil.rmtree(full_path)
        return json.dumps({"status": "deleted_directory", "path": str(full_path)})
    return json.dumps({"error": f"Not a file: {path}"})


async def append_file(path: str, content: str) -> str:
    """Append content to an existing file."""
    from ...config import Config

    full_path = _resolve(path)
    if len(content.encode()) > Config.FILE_SIZE_LIMIT:
        return json.dumps({"error": "Content exceeds FILE_SIZE_LIMIT"})
    full_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(full_path, "a") as f:
        await f.write(content)
    return json.dumps({"status": "appended", "path": str(full_path)})


async def write_binary_file(path: str, content_base64: str) -> str:
    """Create a binary file (images, PDFs, executables) from base64-encoded content."""
    from ...config import Config

    full_path = _resolve(path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    data = base64.b64decode(content_base64)
    if len(data) > Config.FILE_SIZE_LIMIT:
        return json.dumps({"error": "File exceeds FILE_SIZE_LIMIT"})
    async with aiofiles.open(full_path, "wb") as f:
        await f.write(data)
    return json.dumps({"status": "created", "path": str(full_path), "size": len(data), "type": "binary"})


async def copy_file(source: str, destination: str) -> str:
    """Copy a file from source to destination."""
    src = _resolve(source)
    dst = _resolve(destination)
    if not src.exists():
        return json.dumps({"error": f"Source not found: {source}"})
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return json.dumps({"status": "copied", "from": str(src), "to": str(dst)})


async def move_file(source: str, destination: str) -> str:
    """Move/rename a file or directory."""
    src = _resolve(source)
    dst = _resolve(destination)
    if not src.exists():
        return json.dumps({"error": f"Source not found: {source}"})
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return json.dumps({"status": "moved", "from": str(src), "to": str(dst)})


async def create_directory(path: str) -> str:
    """Create a directory including parent directories."""
    full_path = _resolve(path)
    full_path.mkdir(parents=True, exist_ok=True)
    return json.dumps({"status": "created", "path": str(full_path), "type": "directory"})


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
    {
        "type": "function",
        "function": {
            "name": "write_binary_file",
            "description": "Create a binary file (images, PDFs, executables, etc.) from base64-encoded content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content_base64": {"type": "string", "description": "Base64-encoded binary content"},
                },
                "required": ["path", "content_base64"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file from source to destination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move or rename a file or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Create a directory including all parent directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                },
                "required": ["path"],
            },
        },
    },
]
