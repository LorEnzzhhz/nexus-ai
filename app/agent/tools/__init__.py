import json
from .file_tools import FILE_TOOLS, create_file, read_file, list_directory, delete_file, append_file, write_binary_file, copy_file, move_file, create_directory
from .search_tools import SEARCH_TOOLS, web_search, fetch_url
from .shell_tools import SHELL_TOOLS, run_command


ALL_TOOLS = FILE_TOOLS + SEARCH_TOOLS + SHELL_TOOLS

TOOL_REGISTRY = {
    "create_file": create_file,
    "read_file": read_file,
    "list_directory": list_directory,
    "delete_file": delete_file,
    "append_file": append_file,
    "write_binary_file": write_binary_file,
    "copy_file": copy_file,
    "move_file": move_file,
    "create_directory": create_directory,
    "web_search": web_search,
    "fetch_url": fetch_url,
    "run_command": run_command,
}


async def execute_tool(name: str, arguments: dict) -> str:
    func = TOOL_REGISTRY.get(name)
    if not func:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = await func(**arguments)
        return result
    except Exception as e:
        return json.dumps({"error": f"Tool execution error: {e}"})
