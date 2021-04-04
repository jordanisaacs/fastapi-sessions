from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from uuid import uuid4

class SessionBackend(ABC):
    @abstractmethod
    async def read(self, session_id: str) -> Optional[Dict[str, Any]]:
        """ Read sesion data from the storage."""
        raise NotImplementedError()
    
    @abstractmethod
    async def write(self, data: Dict, session_id: Optional[str] = None) -> str:
        """ Write sesion data to the storage"""
        raise NotImplementedError()

    @abstractmethod
    async def remove(self, session_id: str) -> None:
        """ Remove session data from the storage. """
        raise NotImplementedError()

    @abstractmethod
    async def exists(self, sesion_id: str) -> bool:
        """ Test if storage contains session data for a given session_id. """
        raise NotImplementedError()

    async def generate_id(self) -> str:
        """ Generate a new session id. """
        return str(uuid4())