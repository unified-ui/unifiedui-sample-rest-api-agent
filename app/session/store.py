"""In-memory session store for conversation management."""

from __future__ import annotations

import uuid

from unifiedui_sdk.integrations.models import MessageHistoryEntry


class SessionStore:
    """Dict-based in-memory session store."""

    def __init__(self) -> None:
        """Initialize an empty session store."""
        self._sessions: dict[str, list[MessageHistoryEntry]] = {}

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        return session_id

    def get_history(self, session_id: str, limit: int = 20) -> list[MessageHistoryEntry]:
        """Return the last N messages for a session."""
        messages = self._sessions.get(session_id, [])
        return messages[-limit:]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append a message to a session's history."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(MessageHistoryEntry(role=role, content=content))

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._sessions


session_store = SessionStore()
