# Custom Tools

Tools in this directory are registered with the Claude Agent SDK via MCP servers.

## How to Add a New Tool

1. Create a new file: `engine/tools/my_tool.py`
2. Implement an async handler function with the signature `async def my_tool_impl(args: dict) -> dict`
3. Return MCP-formatted responses: `{"content": [{"type": "text", "text": "..."}]}`
4. Register it in `engine/mcp/manager.py` by adding it to the tool definitions

## Built-in Tools

| Tool | File | Status |
|---|---|---|
| `execute_recipe` | `recipe_tool.py` | Implemented — calls LiteLLM directly |
| `query_database` | `database_tool.py` | Placeholder — Supabase integration pending |
| `call_api` | `http_tool.py` | Implemented — makes real HTTP requests |
