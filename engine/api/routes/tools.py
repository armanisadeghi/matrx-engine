"""GET /tools — list available tools and MCP servers."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["tools"])

# Built-in Claude SDK tools
BUILTIN_TOOLS = [
    {"name": "Bash", "description": "Execute shell commands", "source": "builtin"},
    {"name": "Read", "description": "Read file contents", "source": "builtin"},
    {"name": "Write", "description": "Write file contents", "source": "builtin"},
    {"name": "Edit", "description": "Edit files with find/replace", "source": "builtin"},
    {"name": "Glob", "description": "Find files by pattern", "source": "builtin"},
    {"name": "Grep", "description": "Search file contents", "source": "builtin"},
    {"name": "WebSearch", "description": "Search the web", "source": "builtin"},
    {"name": "WebFetch", "description": "Fetch web page content", "source": "builtin"},
]

# Custom tools registered via MCP
CUSTOM_TOOLS = [
    {
        "name": "execute_recipe",
        "description": "Execute a specialized AI recipe for a sub-task via LiteLLM",
        "source": "custom",
    },
    {
        "name": "query_database",
        "description": "Query Supabase/Postgres databases (placeholder)",
        "source": "custom",
    },
    {
        "name": "call_api",
        "description": "Make authenticated HTTP requests to external APIs",
        "source": "custom",
    },
]


@router.get("/tools")
async def list_tools() -> dict:
    """List all tools available to agents."""
    return {"tools": BUILTIN_TOOLS + CUSTOM_TOOLS}
