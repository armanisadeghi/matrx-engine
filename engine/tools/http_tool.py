"""Placeholder: call_api tool — make authenticated HTTP requests to external services.

This is a placeholder implementation. Real HTTP request capabilities
with auth management will be added as integrations are built.
"""

from __future__ import annotations

from typing import Any

import httpx

from engine.utils.logging import get_logger

logger = get_logger(__name__)


async def call_api_impl(args: dict[str, Any]) -> dict[str, Any]:
    """Implementation of the call_api tool.

    Makes an HTTP request to an external API endpoint.

    Args:
        args: Dictionary with url, method, headers, body, timeout.

    Returns:
        MCP-formatted response with the HTTP response data.
    """
    url = args.get("url", "")
    method = args.get("method", "GET").upper()
    headers = args.get("headers", {})
    body = args.get("body", None)
    timeout = args.get("timeout", 30)

    if not url:
        return {
            "content": [{"type": "text", "text": "Error: url is required"}],
            "isError": True,
        }

    logger.info("call_api_called", url=url, method=method)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body and method in ("POST", "PUT", "PATCH") else None,
            )

            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:10000],  # Limit response size
            }

            import json

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    except httpx.TimeoutException:
        return {
            "content": [{"type": "text", "text": f"Error: Request to {url} timed out after {timeout}s"}],
            "isError": True,
        }
    except Exception as exc:
        logger.error("call_api_failed", url=url, error=str(exc))
        return {
            "content": [{"type": "text", "text": f"Error: HTTP request failed: {exc}"}],
            "isError": True,
        }
