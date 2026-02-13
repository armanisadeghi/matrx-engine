"""AgentExecuteRequest and related input models."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class AgentExecuteRequest(BaseModel):
    """Every request to execute an agent starts here."""

    # REQUIRED: The agent/recipe UUID. The recipe system resolves this into a full config.
    id: str = Field(..., description="Agent/Recipe UUID. The recipe system resolves this into a full config.")

    # User's message (optional — some agents are fully autonomous)
    user_input: str | list[dict[str, Any]] | None = None

    # Variables to inject into the recipe template
    variables: dict[str, Any] | None = Field(default_factory=dict)

    # Override specific config values (temperature, max_tokens, model, etc.)
    config_overrides: dict[str, Any] | None = Field(default_factory=dict)

    # Session tracking
    conversation_id: str | None = Field(default_factory=lambda: str(uuid.uuid4()))

    # Execution flags
    stream: bool = True
    debug: bool = False
