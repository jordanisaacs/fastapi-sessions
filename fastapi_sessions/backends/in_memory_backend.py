from typing import Optional, Dict, Any, Type

from fastapi_sessions.backends.session_backend import SessionBackend
from fastapi_sessions.authentication.session_wrapper import (
    SessionData,
    SessionDataWrapper,
)


class InMemoryBackend(SessionBackend):
    """Stores session data in a dictionary."""

    def __init__(self) -> None:
        self.data: Dict[str, Dict[str, Any]] = {}

    async def read(
        self, session_id: str, data_model: Type[SessionData]
    ) -> Optional[SessionDataWrapper[SessionData]]:
        result = self.data.get(session_id)
        if not result:
            return None
        return SessionDataWrapper[data_model](session_id=session_id, **result)

    async def write(self, session_data: SessionDataWrapper[SessionData]) -> bool:
        session_id = session_data.session_id
        self.data[session_id] = session_data.dict(exclude={"session_id"})
        print(self.data)
        return True

    async def update(self, session_id: str) -> bool:
        raise NotImplementedError()

    async def remove(self, session_id: str) -> None:
        if session_id in self.data:
            del self.data[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self.data
