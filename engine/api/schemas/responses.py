"""Response schemas for streaming events, health checks, and tool listings."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class StreamEventResponse(BaseModel):
    """Schema for a single NDJSON streaming event (documentation only)."""

    event: str
    data: dict[str, Any]


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str
    version: str


class ReadyResponse(BaseModel):
    """Response from /ready endpoint."""

    ready: bool
    checks: dict[str, bool]


class ToolInfo(BaseModel):
    """Information about an available tool."""

    name: str
    description: str
    source: str  # "builtin", "custom", "mcp"


class ToolsListResponse(BaseModel):
    """Response from /tools endpoint."""

    tools: list[ToolInfo]
