from typing import Optional, Dict, Any, Type
from pydantic import BaseModel

from fastapi_sessions.backends.session_backend import SessionBackend
from fastapi_sessions.session_wrapper import SessionDataWrapper

class InMemoryBackend(SessionBackend):
    """ Stores session data in a dictionary. """

    def __init__(self) -> None:
        self.data: dict = {}

    async def read(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        result = self.data.get(session_id)
        if not result:
            return None
        print(result)
        return result.copy()

    async def write(self, session_data: SessionDataWrapper[Type[BaseModel]]) -> bool:
        session_id = session_data.session_id
        session_dict = session_data.dict()
        del session_dict['session_id']
        self.data[session_id] = session_dict
        return True

    async def remove(self, session_id: str) -> None:
        del self.data[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self.data
