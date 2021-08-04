"""InMemoryBackend implementation."""
from typing import Dict, Generic

from fastapi_sessions.backends.session_backend import (
    BackendError,
    SessionBackend,
    SessionModel,
)
from fastapi_sessions.frontends.session_frontend import ID


class InMemoryBackend(Generic[ID, SessionModel], SessionBackend[ID, SessionModel]):
    """Stores session data in a dictionary."""

    def __init__(self) -> None:
        """Initialize a new in-memory database."""
        self.data: Dict[ID, SessionModel] = {}

    async def create(self, session_id: ID, data: SessionModel):
        """Create a new session entry."""
        if self.data.get(session_id):
            raise BackendError("create can't overwrite an existing session")

        self.data[session_id] = data.copy(deep=True)

    async def read(self, session_id: ID):
        """Read an existing session data."""
        data = self.data.get(session_id)
        if not data:
            return

        return data.copy(deep=True)

    async def update(self, session_id: ID, data: SessionModel) -> None:
        """Update an existing session."""
        if self.data.get(session_id):
            self.data[session_id] = data
        else:
            raise BackendError("session does not exist, cannot update")

    async def delete(self, session_id: ID) -> None:
        """D"""
        del self.data[session_id]
