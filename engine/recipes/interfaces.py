"""Abstract interface and RecipeResult model — the contract for the Recipe system."""

from __future__ import annotations

import asyncio
import concurrent.futures
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class RecipeResult(BaseModel):
    """The output of recipe resolution. This is the contract.

    The Recipe system ALWAYS returns this shape.
    If it fails, success=False and error is populated.
    If it succeeds, all relevant fields are populated.
    """

    success: bool
    error: str | None = None

    # LLM config
    system_prompt: str = ""
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    max_turns: int | None = None

    # Tool config
    allowed_tools: list[str] | None = None
    custom_tools: list[dict[str, Any]] | None = None
    mcp_servers: list[dict[str, Any]] | None = None

    # Execution config
    permission_mode: str | None = "bypassPermissions"
    compiled_prompt: str | None = None

    # Pass-through
    metadata: dict[str, Any] | None = Field(default_factory=dict)


class RecipeResolverInterface(ABC):
    """Abstract interface for the Recipe system.

    Developers: implement the placeholder. Arman will replace it.
    """

    @abstractmethod
    async def resolve(
        self,
        agent_id: str,
        user_input: str | None = None,
        variables: dict[str, Any] | None = None,
        config_overrides: dict[str, Any] | None = None,
    ) -> RecipeResult:
        """Resolve an agent_id into a full execution config.

        Args:
            agent_id: UUID of the agent/recipe.
            user_input: The user's message (may be empty).
            variables: Template variables to inject.
            config_overrides: Override specific config values.

        Returns:
            RecipeResult with full LLM configuration.
        """
        ...

    def resolve_sync(
        self,
        agent_id: str,
        user_input: str | None = None,
        variables: dict[str, Any] | None = None,
        config_overrides: dict[str, Any] | None = None,
    ) -> RecipeResult:
        """Synchronous version for use inside @tool functions.

        Handles the case where an event loop is already running
        by executing in a thread pool.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.resolve(agent_id, user_input, variables, config_overrides))

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run,
                self.resolve(agent_id, user_input, variables, config_overrides),
            ).result()
