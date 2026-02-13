"""Event type definitions for NDJSON streaming."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """All recognized streaming event types."""

    STATUS = "status"
    CONTENT = "content"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    RECIPE_CALL = "recipe_call"
    ERROR = "error"
    DONE = "done"
    DEBUG = "debug"
    USAGE = "usage"


class StreamEvent(BaseModel):
    """A single NDJSON streaming event."""

    event: EventType
    data: dict[str, Any] = Field(default_factory=dict)

    def to_ndjson(self) -> str:
        """Serialize to a single NDJSON line."""
        return self.model_dump_json() + "\n"
