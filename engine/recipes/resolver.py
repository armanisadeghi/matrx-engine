"""PlaceholderRecipeResolver — default config for any agent_id.

PLACEHOLDER: Returns a sensible default config for any agent_id.
Arman will replace this with the real Recipe system.

For now, this allows the entire engine to be tested end-to-end
without the Recipe system being connected.
"""

from __future__ import annotations

from typing import Any

from engine.recipes.interfaces import RecipeResolverInterface, RecipeResult


class PlaceholderRecipeResolver(RecipeResolverInterface):
    """Returns sensible defaults for any agent_id.

    This enables end-to-end testing of the engine pipeline
    before the real Recipe system is integrated.
    """

    async def resolve(
        self,
        agent_id: str,
        user_input: str | None = None,
        variables: dict[str, Any] | None = None,
        config_overrides: dict[str, Any] | None = None,
    ) -> RecipeResult:
        overrides = config_overrides or {}

        return RecipeResult(
            success=True,
            system_prompt=overrides.get(
                "system_prompt",
                "You are a helpful AI assistant with full access to the local "
                "filesystem and shell. You can read, write, and execute code. "
                "Be thorough and precise.",
            ),
            model=overrides.get("model", None),
            temperature=overrides.get("temperature", None),
            max_tokens=overrides.get("max_tokens", None),
            max_turns=overrides.get("max_turns", 30),
            allowed_tools=overrides.get(
                "allowed_tools",
                [
                    "Bash",
                    "Read",
                    "Write",
                    "Edit",
                    "Glob",
                    "Grep",
                    "WebSearch",
                    "WebFetch",
                    "mcp__matrx_tools__execute_recipe",
                ],
            ),
            permission_mode="bypassPermissions",
            compiled_prompt=user_input,
            metadata={"agent_id": agent_id, "variables": variables or {}},
        )
