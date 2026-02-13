"""LiteLLM proxy management — route the Claude Agent SDK through LiteLLM.

The Claude Agent SDK natively talks to the Anthropic API. By overriding
ANTHROPIC_BASE_URL, we route it through LiteLLM, enabling the SDK's
agent loop to use any model provider.

This is specifically for Layer 1 (Recipe as Agent). Layer 3 (Recipe as Tool)
calls litellm.completion() directly and doesn't need the proxy.
"""

from __future__ import annotations

import os

from engine.utils.logging import get_logger

logger = get_logger(__name__)


def is_proxy_enabled() -> bool:
    """Check if the LiteLLM proxy integration is enabled."""
    return os.getenv("USE_LITELLM_PROXY", "false").lower() in ("true", "1", "yes")


def configure_litellm_proxy() -> None:
    """Point the Claude Agent SDK at LiteLLM proxy instead of Anthropic directly.

    This enables using any model provider through the SDK's agent loop.
    Only activates when USE_LITELLM_PROXY is set to true.

    Must be called BEFORE creating any SDK client.
    """
    if not is_proxy_enabled():
        logger.info("litellm_proxy_disabled", reason="USE_LITELLM_PROXY not set to true")
        return

    proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
    master_key = os.getenv("LITELLM_MASTER_KEY", "")

    os.environ["ANTHROPIC_BASE_URL"] = proxy_url
    if master_key:
        os.environ["ANTHROPIC_API_KEY"] = master_key

    logger.info("litellm_proxy_configured", proxy_url=proxy_url)


def disable_litellm_proxy() -> None:
    """Restore direct Anthropic API access (undo proxy configuration)."""
    if "ANTHROPIC_BASE_URL" in os.environ and is_proxy_enabled():
        del os.environ["ANTHROPIC_BASE_URL"]
        logger.info("litellm_proxy_disabled", reason="manually disabled")
