"""Direct LiteLLM client for Recipe-as-Tool calls.

This module provides a thin wrapper around litellm.completion() for use
by the execute_recipe tool. The proxy is NOT used for this path — LiteLLM
routes directly to the configured provider.
"""

from __future__ import annotations

from typing import Any

import litellm

from engine.utils.logging import get_logger

logger = get_logger(__name__)


class LiteLLMClient:
    """Wrapper around litellm for making direct LLM calls.

    Used by the execute_recipe tool (Layer 3) to call any model provider.
    """

    def __init__(self, default_model: str = "claude-sonnet-4-5-20250929") -> None:
        self._default_model = default_model
        # Suppress litellm's verbose logging by default
        litellm.suppress_debug_info = True

    async def completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Make an async LLM completion call through LiteLLM.

        Args:
            messages: Chat messages in OpenAI format.
            model: Model identifier (e.g., "gpt-4o", "claude-sonnet-4-5-20250929").
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional parameters passed to litellm.

        Returns:
            The completion text content.
        """
        call_model = model or self._default_model

        call_kwargs: dict[str, Any] = {
            "model": call_model,
            "messages": messages,
            **kwargs,
        }
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens

        logger.info("litellm_completion_start", model=call_model, message_count=len(messages))

        try:
            response = await litellm.acompletion(**call_kwargs)
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
                "model": call_model,
            }
            logger.info("litellm_completion_done", **usage)
            return content

        except Exception as exc:
            logger.error("litellm_completion_failed", model=call_model, error=str(exc))
            raise

    def completion_sync(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous LLM completion call (for use inside @tool handlers)."""
        call_model = model or self._default_model

        call_kwargs: dict[str, Any] = {
            "model": call_model,
            "messages": messages,
            **kwargs,
        }
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        if max_tokens is not None:
            call_kwargs["max_tokens"] = max_tokens

        response = litellm.completion(**call_kwargs)
        return response.choices[0].message.content
