### Standard Packages ###
from uuid import UUID, uuid4 as uuid
### Dev Dependencies ###
from pytest import fixture
### Dependencies ###
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel
### Me ###
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.session_verifier import SessionVerifier

@fixture
def setup() -> TestClient:
  ### Classes ###
  class SessionData(BaseModel):
    username: str
  class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__( \
      self, *, identifier: str, auto_error: bool, \
        backend: InMemoryBackend[UUID, SessionData], \
          auth_http_exception: HTTPException,
        ):
      self._identifier = identifier
      self._auto_error = auto_error
      self._backend = backend
      self._auth_http_exception = auth_http_exception
    @property
    def identifier(self): return self._identifier
    @property
    def backend(self): return self._backend
    @property
    def auto_error(self): return self._auto_error
    @property
    def auth_http_exception(self): return self._auth_http_exception
    def verify_session(self, model: SessionData) -> bool: return True

  ### Set up FastAPI App ###
  app: FastAPI                    = FastAPI()

  ### Set up FastAPI Sessions ###
  cookie_params: CookieParameters = CookieParameters()
  cookie = SessionCookie( \
    cookie_name='cookie', identifier='general_verifier', \
      auto_error=True,  secret_key='DONOTUSE', \
        cookie_params=cookie_params, \
      )
  backend = InMemoryBackend[UUID, SessionData]()
  verifier = BasicVerifier( \
    identifier='general_verifier', \
      auto_error=True, backend=backend, \
        auth_http_exception=HTTPException(status_code=403, detail='invalid session'), \
      )

  ### Endpoints ###
  @app.post('/session/{name}', response_class=PlainTextResponse)
  async def create_session(name: str, response: PlainTextResponse):
    session: UUID     = uuid()
    data: SessionData = SessionData(username=name)
    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return 'OK'

  @app.get('/session', dependencies=[Depends(cookie)], response_class=JSONResponse)
  async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data

  @app.delete('/session', response_class=PlainTextResponse)
  async def del_session(response: PlainTextResponse, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"

  ### Returns ###
  return TestClient(app)
