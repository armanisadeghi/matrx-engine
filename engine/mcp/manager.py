"""MCP lifecycle management — loads config, builds servers, attaches to SDK client."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from claude_agent_sdk import tool, create_sdk_mcp_server

from engine.tools.recipe_tool import execute_recipe_impl
from engine.tools.database_tool import query_database_impl
from engine.tools.http_tool import call_api_impl
from engine.utils.logging import get_logger

logger = get_logger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"


class MCPManager:
    """Manages MCP servers for the agent runtime.

    Handles two categories of MCP servers:
    1. Built-in tool server: wraps our custom Python tools as an in-process MCP server
    2. External servers: configured in config.json (e.g., Playwright, GitHub)
    """

    def __init__(self) -> None:
        self._external_configs: list[dict[str, Any]] = []

    def load_config(self, config_path: Path | None = None) -> None:
        """Load external MCP server configurations from config.json."""
        path = config_path or CONFIG_PATH
        if not path.exists():
            logger.warning("mcp_config_not_found", path=str(path))
            return

        try:
            with open(path) as f:
                data = json.load(f)
            self._external_configs = data.get("servers", [])
            logger.info("mcp_config_loaded", server_count=len(self._external_configs))
        except Exception as exc:
            logger.error("mcp_config_load_failed", path=str(path), error=str(exc))

    def get_enabled_external_servers(self) -> list[dict[str, Any]]:
        """Return external server configs that are enabled."""
        enabled = []
        for cfg in self._external_configs:
            if not cfg.get("enabled", False):
                continue
            # Resolve environment variable references in env values
            env = cfg.get("env", {})
            resolved_env = {}
            for key, val in env.items():
                if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
                    env_var = val[2:-1]
                    resolved_env[key] = os.environ.get(env_var, "")
                else:
                    resolved_env[key] = val
            cfg_copy = {**cfg, "env": resolved_env}
            enabled.append(cfg_copy)
        return enabled

    def build_tools_mcp_server(self) -> Any:
        """Build the in-process MCP server containing all custom tools.

        Returns a server object compatible with ClaudeAgentOptions.mcp_servers.
        """
        execute_recipe = tool(
            name="execute_recipe",
            description=(
                "Execute a specialized AI recipe for a specific task. Use this when you need "
                "expert-level processing for a sub-task such as: content generation, analysis, "
                "translation, code review, data extraction, summarization, or any task that "
                "benefits from a specialized, pre-configured AI agent."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "recipe_id": {
                        "type": "string",
                        "description": "The UUID of the recipe to execute.",
                    },
                    "task_description": {
                        "type": "string",
                        "description": "What you need this recipe to do. Be specific.",
                    },
                    "variables": {
                        "type": "object",
                        "description": "Key-value pairs of variables the recipe needs.",
                        "default": {},
                    },
                    "config_overrides": {
                        "type": "object",
                        "description": "Optional overrides (temperature, model, max_tokens).",
                        "default": {},
                    },
                },
                "required": ["recipe_id", "task_description"],
            },
        )(execute_recipe_impl)

        query_database = tool(
            name="query_database",
            description=(
                "Query a database (Supabase/Postgres). Accepts SQL queries or structured queries. "
                "Use this for data retrieval, analytics, or any database operation."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query or structured query to execute.",
                    },
                    "database": {
                        "type": "string",
                        "description": "Which database to query. Defaults to 'default'.",
                        "default": "default",
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters for parameterized queries.",
                        "default": {},
                    },
                },
                "required": ["query"],
            },
        )(query_database_impl)

        call_api = tool(
            name="call_api",
            description=(
                "Make an authenticated HTTP request to an external API. "
                "Supports GET, POST, PUT, PATCH, DELETE methods."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to request.",
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, PATCH, DELETE).",
                        "default": "GET",
                    },
                    "headers": {
                        "type": "object",
                        "description": "HTTP headers to include.",
                        "default": {},
                    },
                    "body": {
                        "type": "object",
                        "description": "Request body (for POST/PUT/PATCH).",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Request timeout in seconds.",
                        "default": 30,
                    },
                },
                "required": ["url"],
            },
        )(call_api_impl)

        server = create_sdk_mcp_server(
            name="matrx_tools",
            version="0.1.0",
            tools=[execute_recipe, query_database, call_api],
        )

        logger.info("tools_mcp_server_built", tool_count=3)
        return server
