from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from itsdangerous import URLSafeTimedSerializer
from base64 import b64encode
from os import urandom


class SessionBackend(ABC):
    @abstractmethod
    async def read(self, session_id: str) -> Optional[Dict[str, Any]]:
        """ Read sesion data from the storage."""
        raise NotImplementedError()

    @abstractmethod
    async def write(
        self,
        data: Dict,
        serializer: URLSafeTimedSerializer,
    ) -> Tuple[str, str]:
        """ Write sesion data to the storage"""
        raise NotImplementedError()

    @abstractmethod
    async def update(self, data: Dict, session_id: str):
        raise NotImplementedError()

    @abstractmethod
    async def remove(self, session_id: str) -> None:
        """ Remove session data from the storage. """
        raise NotImplementedError()

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """ Test if storage contains session data for a given session_id. """
        raise NotImplementedError()

    def generate_token(self, serializer: URLSafeTimedSerializer) -> str:
        """ Generate a new CSPRNG and signs it. """
        return serializer.dumps(b64encode(urandom(64)).encode("utf-8"))
