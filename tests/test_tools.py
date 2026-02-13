"""Tests for the tool registry and tool implementations."""

from __future__ import annotations

import pytest

from engine.tools.registry import ToolRegistry


def test_registry_register_and_get() -> None:
    reg = ToolRegistry()

    def my_tool() -> str:
        return "result"

    reg.register(my_tool)
    assert len(reg.get_all()) == 1
    assert reg.get_all()[0] is my_tool


def test_registry_get_by_names() -> None:
    reg = ToolRegistry()

    def tool_a() -> str:
        return "a"

    def tool_b() -> str:
        return "b"

    def tool_c() -> str:
        return "c"

    reg.register(tool_a)
    reg.register(tool_b)
    reg.register(tool_c)

    result = reg.get_by_names(["tool_a", "tool_c"])
    assert len(result) == 2
    assert result[0] is tool_a
    assert result[1] is tool_c


def test_registry_get_names() -> None:
    reg = ToolRegistry()

    def alpha() -> str:
        return ""

    def beta() -> str:
        return ""

    reg.register(alpha)
    reg.register(beta)

    names = reg.get_names()
    assert "alpha" in names
    assert "beta" in names


def test_registry_duplicate_registration() -> None:
    reg = ToolRegistry()

    def dup_tool() -> str:
        return ""

    reg.register(dup_tool)
    reg.register(dup_tool)  # Should not add twice

    assert len(reg.get_all()) == 1


async def test_database_tool_placeholder() -> None:
    from engine.tools.database_tool import query_database_impl

    result = await query_database_impl({"query": "SELECT 1"})
    assert "content" in result
    assert "PLACEHOLDER" in result["content"][0]["text"]


async def test_database_tool_requires_query() -> None:
    from engine.tools.database_tool import query_database_impl

    result = await query_database_impl({})
    assert result.get("isError") is True


async def test_http_tool_requires_url() -> None:
    from engine.tools.http_tool import call_api_impl

    result = await call_api_impl({})
    assert result.get("isError") is True


async def test_recipe_tool_requires_fields() -> None:
    from engine.tools.recipe_tool import execute_recipe_impl

    result = await execute_recipe_impl({})
    assert result.get("isError") is True
    assert "recipe_id" in result["content"][0]["text"]

    result2 = await execute_recipe_impl({"recipe_id": "test"})
    assert result2.get("isError") is True
    assert "task_description" in result2["content"][0]["text"]
