import sys
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import List, Generic
from redis.client import Redis
import redis
import json

sys.path.append("..")

from fastapi_sessions.frontends.implementations import CookieParameters  # noqa
from fastapi_sessions.frontends.implementations import SessionCookie  # noqa
from fastapi_sessions.session_verifier import SessionVerifier  # noqa
from fastapi_sessions.backends.session_backend import ( # noqa
    BackendError,
    SessionBackend,
    SessionModel,
)
from fastapi_sessions.frontends.session_frontend import ID # noqa


class InRedisBackend(Generic[ID, SessionModel], SessionBackend[ID, SessionModel]):
    """Stores session data in a dictionary."""

    def __init__(self, connect: Redis, cls: SessionModel) -> None:
        """
        Initialize a new in-redis database.

            Parameters:
                connect (Redis): open connection with redis
                cls (SessionModel): actual model for session data
        """
        self._connect = connect
        self._cls = cls

    async def create(self, session_id: ID, data: SessionModel):
        """Create a new session entry."""
        if self._connect.get(str(session_id)):
            raise BackendError("create can't overwrite an existing session")

        self._connect.set(str(session_id), data.json())

    async def read(self, session_id: ID):
        """Read an existing session data."""
        data = self._connect.get(str(session_id))
        if not data:
            return

        model = self._cls(**json.loads(data))
        return model

    async def update(self, session_id: ID, data: SessionModel) -> None:
        """Update an existing session."""
        if self._connect.get(str(session_id)):
            self._connect.set(str(session_id), data.json())
        else:
            raise BackendError("session does not exist, cannot update")

    async def delete(self, session_id: ID) -> None:
        """Delete"""
        self._connect.delete(str(session_id))


class InnerData(BaseModel):
    id: int
    data: str


class SessionData(BaseModel):
    """complex model with nested fields"""
    username: str
    data: List[InnerData]


cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)

connect = redis.Redis(host='localhost', port='6379', db=0)
# Maybe there is a better way to get `SessionData` from generic construction
backend = InRedisBackend[UUID, SessionData](connect, SessionData)


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InRedisBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)

app = FastAPI()


@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):

    session = uuid4()
    data = SessionData(username=name, data=[
        InnerData(id=1, data='one'),
        InnerData(id=2, data='two'),
        InnerData(id=3, data='three')])

    await backend.create(session, data)
    cookie.attach_to_response(response, session)

    return f"created session with {data=}"


@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data


@app.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"
