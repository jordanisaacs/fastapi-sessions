from typing import Optional, Dict
from fastapi_sessions.backends.session_backend import SessionBackend


class InMemoryBackend(SessionBackend):
    """ Stores session data in a dictionary. """

    def __init__(self) -> None:
        self.data: dict = {}

    async def read(self, session_id: str) -> Optional[Dict]:
        result = self.data.get(session_id)
        if not result:
            return result
        return result.copy()

    async def write(
        self,
        session_data: Dict,
        session_id: Optional[str] = None,
    ) -> str:
        session_id = session_id or await self.generate_id()
        self.data[session_id] = session_data
        return session_id

    async def remove(self, session_id: str) -> None:
        del self.data[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self.data
