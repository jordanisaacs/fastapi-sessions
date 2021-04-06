from typing import Optional, Dict, Any, Type

from pydantic import BaseModel

from .session_backend import SessionBackend
from fastapi_sessions.authentication.session_wrapper import SessionDataWrapper


class InMemoryBackend(SessionBackend):
    """Stores session data in a dictionary."""

    def __init__(self) -> None:
        self.data: Dict[str, Dict[str, Any]] = {}

    async def read(
        self, session_id: str, data_model: Type[BaseModel]
    ) -> Optional[SessionDataWrapper[BaseModel]]:
        result = self.data.get(session_id)
        if not result:
            return None
        return SessionDataWrapper[data_model](session_id=session_id, **result)

    async def write(self, session_data: SessionDataWrapper[BaseModel]) -> bool:
        session_id = session_data.session_id
        self.data[session_id] = session_data.dict(exclude={"session_id"})
        return True

    async def remove(self, session_id: str) -> None:
        del self.data[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self.data
