from typing import Optional, Dict
from itsdangerous import URLSafeTimedSerializer
from fastapi_sessions.backends.session_backend import SessionBackend


class InMemoryBackend(SessionBackend):
    """ Stores session data in a dictionary. """

    def __init__(self) -> None:
        self.data: dict = {}

    async def read(
        self,
        session_id: str,
        serializer: URLSafeTimedSerializer,
    ) -> Optional[Dict]:
        result = self.data.get(session_id)
        if not result:
            return None
        return result.copy()

    async def write(
        self,
        session_data: Dict,
        serializer: URLSafeTimedSerializer,
    ) -> str:
        session_id = self.generate_token()
        csrf_token = self.generate_token()

        session_data["csrf_token"] = csrf_token
        self.data[session_id] = session_data

        return serializer.dump(session_id), serializer.dump(csrf_token)

    async def remove(self, session_id: str) -> None:
        del self.data[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self.data
