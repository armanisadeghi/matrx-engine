"""Session management — conversation continuity across requests.

Tracks active sessions so agents can resume previous conversations.
The real persistence layer (database-backed) will be added by Arman.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentSession:
    """Represents an active or completed agent session."""

    session_id: str
    conversation_id: str
    agent_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """In-memory session store. Will be replaced with persistent storage."""

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    def create_session(self, agent_id: str, conversation_id: str | None = None) -> AgentSession:
        """Create a new agent session."""
        session = AgentSession(
            session_id=str(uuid.uuid4()),
            conversation_id=conversation_id or str(uuid.uuid4()),
            agent_id=agent_id,
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> AgentSession | None:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)

    def end_session(self, session_id: str) -> None:
        """Mark a session as completed."""
        session = self._sessions.get(session_id)
        if session:
            session.ended_at = datetime.now(timezone.utc)
            session.status = "completed"

    def get_by_conversation(self, conversation_id: str) -> list[AgentSession]:
        """Get all sessions for a conversation."""
        return [s for s in self._sessions.values() if s.conversation_id == conversation_id]
