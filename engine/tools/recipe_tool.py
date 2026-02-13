"""THE KEY TOOL: execute_recipe — executes a Recipe as a tool call via LiteLLM.

When Claude's agent loop encounters a task that a specialized Recipe handles
better, it calls this tool. Under the hood, a completely separate LLM call
happens via LiteLLM — Claude just gets the result back as a string.
"""

from __future__ import annotations

from typing import Any

from engine.utils.logging import get_logger

logger = get_logger(__name__)

# Lazy-loaded references set during app startup
_recipe_resolver = None
_litellm_client = None


def configure_recipe_tool(recipe_resolver: Any, litellm_client: Any) -> None:
    """Wire the recipe tool with its dependencies at startup."""
    global _recipe_resolver, _litellm_client
    _recipe_resolver = recipe_resolver
    _litellm_client = litellm_client


async def execute_recipe_impl(args: dict[str, Any]) -> dict[str, Any]:
    """Implementation of the execute_recipe tool.

    Called by the MCP server when Claude invokes this tool.

    Args:
        args: Dictionary with recipe_id, task_description, variables, config_overrides.

    Returns:
        MCP-formatted response with text content.
    """
    recipe_id: str = args.get("recipe_id", "")
    task_description: str = args.get("task_description", "")
    variables: dict[str, Any] = args.get("variables", {})
    config_overrides: dict[str, Any] = args.get("config_overrides", {})

    if not recipe_id:
        return _error_response("recipe_id is required")

    if not task_description:
        return _error_response("task_description is required")

    if _recipe_resolver is None:
        return _error_response("Recipe resolver not initialized")

    logger.info("execute_recipe_called", recipe_id=recipe_id, task=task_description[:100])

    try:
        # 1. Resolve recipe config
        recipe_result = _recipe_resolver.resolve_sync(
            agent_id=recipe_id,
            user_input=task_description,
            variables=variables,
            config_overrides=config_overrides,
        )

        if not recipe_result.success:
            return _error_response(f"Recipe resolution failed: {recipe_result.error}")

        # 2. Make LLM call directly through LiteLLM (NOT through Claude Agent SDK)
        import litellm

        model = recipe_result.model or "claude-sonnet-4-5-20250929"
        messages = [
            {"role": "system", "content": recipe_result.system_prompt},
            {"role": "user", "content": recipe_result.compiled_prompt or task_description},
        ]

        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if recipe_result.temperature is not None:
            kwargs["temperature"] = recipe_result.temperature
        if recipe_result.max_tokens is not None:
            kwargs["max_tokens"] = recipe_result.max_tokens

        response = litellm.completion(**kwargs)
        result_text = response.choices[0].message.content

        logger.info(
            "execute_recipe_completed",
            recipe_id=recipe_id,
            model=model,
            tokens=getattr(response.usage, "total_tokens", None),
        )

        return {"content": [{"type": "text", "text": result_text}]}

    except Exception as exc:
        logger.error("execute_recipe_failed", recipe_id=recipe_id, error=str(exc))
        return _error_response(f"Recipe execution failed: {exc}")


def _error_response(message: str) -> dict[str, Any]:
    """Build an MCP error response."""
    return {"content": [{"type": "text", "text": f"Error: {message}"}], "isError": True}
