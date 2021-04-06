from typing import Optional, Type
from abc import ABC, abstractmethod

from pydantic.main import BaseModel

from fastapi_sessions.authentication.session_wrapper import SessionDataWrapper


class SessionBackend(ABC):
    @abstractmethod
    async def read(
        self, session_id: str, data_model: Type[BaseModel]
    ) -> Optional[SessionDataWrapper[BaseModel]]:
        """Read session data from the storage."""
        raise NotImplementedError()

    @abstractmethod
    async def write(self, session_data: SessionDataWrapper[BaseModel]) -> bool:
        """Write new session data to the storage"""
        raise NotImplementedError()

    @abstractmethod
    async def remove(self, session_id: str) -> None:
        """Remove session data from the storage. """
        raise NotImplementedError()

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Test if storage contains session data for a given session_id. """
        raise NotImplementedError()
