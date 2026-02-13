"""POST /agent/execute — primary endpoint for agent execution.

Accepts an AgentExecuteRequest, resolves the recipe, runs the agent,
and streams results back as NDJSON.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from engine.api.middleware.auth import verify_user
from engine.api.schemas.requests import AgentExecuteRequest
from engine.streaming import StreamEmitter
from engine.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["agent"])


@router.post("/agent/execute")
async def execute_agent(
    body: AgentExecuteRequest,
    request: Request,
    user: dict[str, Any] = Depends(verify_user),
) -> StreamingResponse:
    """Execute an agent and stream NDJSON results.

    The agent executor is injected via app state (set up in main.py lifespan).
    """
    executor = request.app.state.executor

    emitter = StreamEmitter(debug=body.debug)

    # Launch agent execution as a background task so streaming starts immediately
    async def run_agent() -> None:
        try:
            await executor.execute(body, emitter)
        except Exception as exc:
            logger.error("agent_route_error", error=str(exc), exc_info=True)
            await emitter.emit_error(f"Unexpected error: {exc}")
        finally:
            # Ensure the stream is always closed
            await emitter.close()

    task = asyncio.create_task(run_agent())

    # Attach task to app state for potential cleanup
    if not hasattr(request.app.state, "active_tasks"):
        request.app.state.active_tasks = set()
    request.app.state.active_tasks.add(task)
    task.add_done_callback(lambda t: request.app.state.active_tasks.discard(t))

    return StreamingResponse(
        emitter,
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "X-Conversation-ID": body.conversation_id or "",
        },
    )
