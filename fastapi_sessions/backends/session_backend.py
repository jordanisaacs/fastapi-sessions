from typing import Optional, Type
from abc import ABC, abstractmethod

from fastapi_sessions.authentication.session_wrapper import (
    SessionDataWrapper,
    SessionData,
)


class SessionBackend(ABC):
    @abstractmethod
    async def read(
        self, session_id: str, data_model: Type[SessionData]
    ) -> Optional[SessionDataWrapper[SessionData]]:
        """Read session data from the storage."""
        raise NotImplementedError()

    @abstractmethod
    async def write(self, session_data: SessionDataWrapper[SessionData]) -> bool:
        """Write new session data to the storage"""
        raise NotImplementedError()

    @abstractmethod
    async def update(self, session_id: str) -> bool:
        """Update existing session data"""
        raise NotImplementedError()

    @abstractmethod
    async def remove(self, session_id: str) -> None:
        """Remove session data from the storage. """
        raise NotImplementedError()

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Test if storage contains session data for a given session_id. """
        raise NotImplementedError()
