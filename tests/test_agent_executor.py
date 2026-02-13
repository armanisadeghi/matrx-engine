"""Tests for the AgentExecutor (mocked SDK calls)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from engine.agent.executor import AgentExecutor
from engine.agent.permissions import PermissionMode, resolve_permission_mode
from engine.agent.session import SessionManager
from engine.api.schemas.requests import AgentExecuteRequest
from engine.mcp import MCPManager
from engine.recipes import PlaceholderRecipeResolver, RecipeResult
from engine.streaming import StreamEmitter


def test_resolve_permission_mode_valid() -> None:
    assert resolve_permission_mode("bypassPermissions") == "bypassPermissions"
    assert resolve_permission_mode("acceptEdits") == "acceptEdits"
    assert resolve_permission_mode("prompt") == "prompt"


def test_resolve_permission_mode_invalid() -> None:
    assert resolve_permission_mode("invalid") == "bypassPermissions"
    assert resolve_permission_mode(None) == "bypassPermissions"


def test_resolve_permission_mode_custom_default() -> None:
    assert resolve_permission_mode(None, default="acceptEdits") == "acceptEdits"


def test_session_manager_create_and_get() -> None:
    sm = SessionManager()
    session = sm.create_session(agent_id="test-agent")
    assert session.agent_id == "test-agent"
    assert session.status == "active"

    retrieved = sm.get_session(session.session_id)
    assert retrieved is session


def test_session_manager_end_session() -> None:
    sm = SessionManager()
    session = sm.create_session(agent_id="test-agent")
    sm.end_session(session.session_id)
    assert session.status == "completed"
    assert session.ended_at is not None


async def test_executor_emits_error_on_failed_recipe() -> None:
    """When recipe resolution fails, executor should emit an error event."""
    resolver = AsyncMock()
    resolver.resolve.return_value = RecipeResult(
        success=False,
        error="Recipe not found",
    )

    mcp = MagicMock(spec=MCPManager)
    sm = SessionManager()

    executor = AgentExecutor(
        recipe_resolver=resolver,
        mcp_manager=mcp,
        session_manager=sm,
        workspace_path="/tmp/test",
    )

    emitter = StreamEmitter(debug=False)
    request = AgentExecuteRequest(id="bad-uuid", user_input="test")

    # Run executor in background
    async def run() -> None:
        await executor.execute(request, emitter)

    task = asyncio.create_task(run())

    events: list[str] = []
    async for line in emitter:
        events.append(line)

    await task

    # Should have status + error events
    parsed = [json.loads(e) for e in events]
    event_types = [e["event"] for e in parsed]
    assert "status" in event_types
    assert "error" in event_types

    error_event = next(e for e in parsed if e["event"] == "error")
    assert "Recipe not found" in error_event["data"]["error"]


async def test_executor_emits_error_on_empty_prompt() -> None:
    """When no prompt is available, executor should emit an error."""
    resolver = PlaceholderRecipeResolver()
    mcp = MagicMock(spec=MCPManager)
    sm = SessionManager()

    executor = AgentExecutor(
        recipe_resolver=resolver,
        mcp_manager=mcp,
        session_manager=sm,
        workspace_path="/tmp/test",
    )

    emitter = StreamEmitter(debug=False)
    # No user_input, resolver will set compiled_prompt to None
    request = AgentExecuteRequest(id="test-uuid", user_input=None)

    task = asyncio.create_task(executor.execute(request, emitter))

    events: list[str] = []
    async for line in emitter:
        events.append(line)

    await task

    parsed = [json.loads(e) for e in events]
    event_types = [e["event"] for e in parsed]
    assert "error" in event_types
