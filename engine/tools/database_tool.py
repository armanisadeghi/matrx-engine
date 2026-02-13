"""Placeholder: query_database tool — query Supabase/Postgres.

This is a placeholder implementation. The real database connection
will be added when Arman integrates the Supabase backend.
"""

from __future__ import annotations

from typing import Any

from engine.utils.logging import get_logger

logger = get_logger(__name__)


async def query_database_impl(args: dict[str, Any]) -> dict[str, Any]:
    """Placeholder implementation for the query_database tool.

    Args:
        args: Dictionary with query, database, and params.

    Returns:
        MCP-formatted response.
    """
    query = args.get("query", "")
    database = args.get("database", "default")

    if not query:
        return {
            "content": [{"type": "text", "text": "Error: query is required"}],
            "isError": True,
        }

    logger.info("query_database_called", database=database, query=query[:100])

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"[PLACEHOLDER] Database tool not yet connected. "
                    f"Would execute on '{database}': {query}"
                ),
            }
        ]
    }
