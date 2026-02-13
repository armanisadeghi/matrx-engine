"""Tests for the PlaceholderRecipeResolver."""

from __future__ import annotations

import pytest

from engine.recipes import PlaceholderRecipeResolver


@pytest.fixture
def resolver() -> PlaceholderRecipeResolver:
    return PlaceholderRecipeResolver()


async def test_resolve_returns_success(resolver: PlaceholderRecipeResolver) -> None:
    result = await resolver.resolve(agent_id="test-uuid-1234")
    assert result.success is True
    assert result.error is None


async def test_resolve_includes_system_prompt(resolver: PlaceholderRecipeResolver) -> None:
    result = await resolver.resolve(agent_id="test-uuid")
    assert "helpful AI assistant" in result.system_prompt


async def test_resolve_includes_default_tools(resolver: PlaceholderRecipeResolver) -> None:
    result = await resolver.resolve(agent_id="test-uuid")
    assert result.allowed_tools is not None
    assert "Bash" in result.allowed_tools
    assert "Read" in result.allowed_tools
    assert "Write" in result.allowed_tools


async def test_resolve_passes_user_input_as_compiled_prompt(resolver: PlaceholderRecipeResolver) -> None:
    result = await resolver.resolve(agent_id="test-uuid", user_input="Hello world")
    assert result.compiled_prompt == "Hello world"


async def test_resolve_stores_variables_in_metadata(resolver: PlaceholderRecipeResolver) -> None:
    result = await resolver.resolve(
        agent_id="test-uuid",
        variables={"key": "value"},
    )
    assert result.metadata is not None
    assert result.metadata["variables"] == {"key": "value"}


async def test_resolve_applies_config_overrides(resolver: PlaceholderRecipeResolver) -> None:
    result = await resolver.resolve(
        agent_id="test-uuid",
        config_overrides={"model": "gpt-4o", "temperature": 0.5},
    )
    assert result.model == "gpt-4o"
    assert result.temperature == 0.5


async def test_resolve_default_permission_mode(resolver: PlaceholderRecipeResolver) -> None:
    result = await resolver.resolve(agent_id="test-uuid")
    assert result.permission_mode == "bypassPermissions"


async def test_resolve_sync_works(resolver: PlaceholderRecipeResolver) -> None:
    result = resolver.resolve_sync(agent_id="test-uuid", user_input="sync test")
    assert result.success is True
    assert result.compiled_prompt == "sync test"
