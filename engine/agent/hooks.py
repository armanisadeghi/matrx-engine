"""Pre/post execution hooks for the agent lifecycle."""

from __future__ import annotations

from typing import Any

from engine.streaming import StreamEmitter
from engine.utils.logging import get_logger

logger = get_logger(__name__)


async def pre_execution_hook(
    agent_id: str,
    prompt: str,
    emitter: StreamEmitter,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Called before the agent starts executing.

    Use this to set up workspace state, validate preconditions,
    or emit initial status events.
    """
    await emitter.emit_status("initializing", agent_id=agent_id)
    logger.info("pre_execution", agent_id=agent_id, prompt_length=len(prompt))


async def post_execution_hook(
    agent_id: str,
    result: str | None,
    emitter: StreamEmitter,
    usage: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Called after the agent finishes executing.

    Use this for cleanup, usage tracking, or final status emission.
    """
    if error:
        logger.error("post_execution_error", agent_id=agent_id, error=error)
    else:
        logger.info("post_execution_success", agent_id=agent_id, has_result=result is not None)

    if usage:
        await emitter.emit_usage(usage)
