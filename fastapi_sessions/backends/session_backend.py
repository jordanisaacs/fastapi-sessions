from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

class SessionBackend(ABC):
    @abstractmethod
    async def read(self, session_id: str) -> Optional[Dict[str, Any]]:
        """ Read session data from the storage."""
        raise NotImplementedError()

    @abstractmethod
    async def write(
        self,
        data: 'SessionDataWrapper[SessionData]'
    ) -> bool:
        """ Write session data to the storage"""
        raise NotImplementedError()

    @abstractmethod
    async def remove(self, session_id: str) -> None:
        """ Remove session data from the storage. """
        raise NotImplementedError()

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """ Test if storage contains session data for a given session_id. """
        raise NotImplementedError()
