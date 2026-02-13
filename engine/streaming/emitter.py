"""StreamEmitter — NDJSON event streaming to clients."""

from __future__ import annotations

import asyncio
from typing import Any

from engine.streaming.events import EventType, StreamEvent
from engine.utils.logging import get_logger

logger = get_logger(__name__)


class StreamEmitter:
    """Manages an async queue of StreamEvents for NDJSON responses.

    The FastAPI route creates an emitter, passes it to the executor,
    and yields events from it via StreamingResponse.
    """

    def __init__(self, debug: bool = False) -> None:
        self._queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue()
        self._debug = debug
        self._closed = False

    async def emit(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Emit an event to the stream."""
        if self._closed:
            return
        event = StreamEvent(event=event_type, data=data)
        await self._queue.put(event)

    async def emit_status(self, status: str, **extra: Any) -> None:
        """Emit a status event."""
        await self.emit(EventType.STATUS, {"status": status, **extra})

    async def emit_content(self, text: str) -> None:
        """Emit a content event with text from the agent."""
        await self.emit(EventType.CONTENT, {"text": text})

    async def emit_tool_use(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        """Emit a tool_use event."""
        await self.emit(EventType.TOOL_USE, {"tool": tool_name, "input": tool_input})

    async def emit_tool_result(self, tool_name: str, result: str) -> None:
        """Emit a tool_result event."""
        await self.emit(EventType.TOOL_RESULT, {"tool": tool_name, "result": result})

    async def emit_recipe_call(self, recipe_id: str, task: str) -> None:
        """Emit a recipe_call event for sub-agent visibility."""
        await self.emit(EventType.RECIPE_CALL, {"recipe_id": recipe_id, "task": task})

    async def emit_error(self, error: str, details: dict[str, Any] | None = None) -> None:
        """Emit an error event."""
        await self.emit(EventType.ERROR, {"error": error, **(details or {})})

    async def emit_done(self, result: str | None = None, usage: dict[str, Any] | None = None) -> None:
        """Emit a done event and close the stream."""
        data: dict[str, Any] = {}
        if result is not None:
            data["result"] = result
        if usage is not None:
            data["usage"] = usage
        await self.emit(EventType.DONE, data)
        await self.close()

    async def emit_debug(self, info: dict[str, Any]) -> None:
        """Emit a debug event (only if debug mode is active)."""
        if self._debug:
            await self.emit(EventType.DEBUG, info)

    async def emit_usage(self, usage: dict[str, Any]) -> None:
        """Emit a usage/cost tracking event."""
        await self.emit(EventType.USAGE, usage)

    async def close(self) -> None:
        """Signal the end of the stream."""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)

    async def __aiter__(self):
        """Async iterator for consuming events."""
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield event.to_ndjson()
