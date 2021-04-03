from datetime import timedelta, datetime
from typing import Type, Optional, Dict, Any, Tuple
from uuid import uuid4
from abc import ABC, abstractmethod

from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.security.api_key import APIKeyBase, APIKey, APIKeyIn
from base64 import b64encode, b64decode
from itsdangerous import TimestampSigner
from itsdangerous.exc import BadTimeSignature, SignatureExpired

from pydantic import BaseModel

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

class InMemoryBackend(SessionBackend):
    """ Stores session data in a dictionary. """

    def __init__(self) -> None:
        print("initalized")
        self.data: dict = {}
    
    async def read(self, session_id: str) -> Optional[Dict]:
        result = self.data.get(session_id)
        if not result:
            return result
        return result.copy()
    
    async def write(self, session_data: Dict, session_id: Optional[str] = None) -> str:
        session_id = session_id or await self.generate_id()
        self.data[session_id] = session_data
        return session_id
    
    async def remove(self, session_id: str) -> None:
        del self.data[session_id]
    
    async def exists(self, session_id: str) -> bool:
        return session_id in self.data

class SessionCookie(APIKeyBase):
    def __init__(
        self,
        *,
        name: str,
        secret_key: str,
        data_model: Type[BaseModel],
        backend: Type[SessionBackend],
        scheme_name: Optional[str] = None,
        auto_error: bool = True,
        max_age: timedelta = timedelta(days=14),
        expires: datetime = None,
        path: str = "/",
        domain: str = None,
        https_only: bool = False,
        httponly: bool = True,
        samesite: str = "strict",
    ):
        self.model: APIKey = APIKey(**{"in": APIKeyIn.cookie}, name=name)
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

        self.signer = TimestampSigner(secret_key)
        self.backend = backend
        self.data_model = data_model

        self.max_age = max_age
        self.expires = expires
        self.path = path
        self.domain = domain
        self.https_only = https_only
        self.httponly = httponly
        self.samesite = samesite
    
    async def __call__(self, request: Request) -> Optional[str]:
        api_key = request.cookies.get(self.model.name)
        if not api_key:
            print("test")
            if self.auto_error:
                raise HTTPException(
                    status_code=403,
                    detail="Not authenticated"
                )
            else:
                return None
        
        try:
            decode_api_key = b64decode(api_key.encode('utf-8'))
            session_id = self.signer.unsign(decode_api_key, max_age=self.max_age.total_seconds(), return_timestamp=False).decode('utf-8')
        except Exception as e:
            if self.auto_error:
                detail = "Not authenticated: "
                detail += "Session expired" if e is SignatureExpired else "Session altered"
                raise HTTPException(
                    status_code=403,
                    detail=detail
                )
            else:
                return None

        session_data = await self.backend.read(session_id)
        if not session_data:
            if self.auto_error:
                raise HTTPException(
                    status_code=403,
                    detail="Not authenticated. Invalid session"
                )
            else:
                return None
        
        return session_data, session_id
    
    async def start_and_set_session(self, data: Type[BaseModel], response: Response):
        if type(data) is not self.data_model:
            raise TypeError("Data is not of right type")
        session_id = self.signer.sign(await self.backend.write(data))
        session_id = b64encode(session_id).decode('utf-8')
        
        response.set_cookie(
            key=self.model.name,
            value=session_id,
            max_age=self.max_age.total_seconds(),
            expires=self.expires,
            path=self.path,
            domain=self.domain,            
            secure=self.https_only,
            httponly=self.httponly,
            samesite=self.samesite,
        )
        return

    async def end_and_delete_session(self, session: Optional[str], response: Response):
        response.delete_cookie(self.model.name)
        if session is not None:
            await self.backend.remove(session[1])
        return

test_app = FastAPI()

class SessionData(BaseModel):
    username: str

test_session = SessionCookie(
    name="session",
    secret_key="helloworld",
    data_model=SessionData,
    backend=InMemoryBackend(),
    scheme_name="Test Cookies",
    auto_error=False
)

@test_app.get("/secure")
async def secure_thing(session: Tuple[SessionData, str] = Depends(test_session)):
    if session is None:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated"
        )
    return {"message": "You are secure", "user": session[0]}

@test_app.post("/get_session")
async def login(username: str, response: Response):
    test_user = SessionData(username=username)
    await test_session.start_and_set_session(test_user, response)
    return {"message": "You now have a session", "user": test_user}

@test_app.post("/leave_session")
async def logout(response: Response, session: Optional[Tuple[SessionData, str]] = Depends(test_session)):
    await test_session.end_and_delete_session(session, response)
    return {"message": "You now don't have a session", "user": session}