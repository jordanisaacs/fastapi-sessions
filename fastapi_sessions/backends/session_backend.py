"""Generic backend code."""
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from fastapi_sessions.frontends.session_frontend import ID
from pydantic.main import BaseModel

SessionModel = TypeVar("SessionModel", bound=BaseModel)


class BackendError(Exception):
    """Error that is thrown by backends."""

    pass


class SessionBackend(ABC, Generic[ID, SessionModel]):
    """Abstract class that defines methods for interacting with session data."""

    @abstractmethod
    async def create(self, session_id: ID, data: SessionModel) -> None:
        """Create a new session."""
        raise NotImplementedError()

    @abstractmethod
    async def read(self, session_id: ID) -> Optional[SessionModel]:
        """Read session data from the storage."""
        raise NotImplementedError()

    @abstractmethod
    async def update(self, session_id: ID, data: SessionModel) -> None:
        """Update session data to the storage"""
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, session_id: ID) -> None:
        """Remove session data from the storage."""
        raise NotImplementedError()
