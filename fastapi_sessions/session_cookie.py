from typing import Type, Optional, Dict, Any, Tuple, NewType
from datetime import timedelta, datetime

from base64 import b64encode, b64decode

from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.security.api_key import APIKeyBase, APIKey, APIKeyIn

from itsdangerous import TimestampSigner
from itsdangerous.exc import BadTimeSignature, SignatureExpired

from pydantic import BaseModel

from fastapi_sessions.backends import InMemoryBackend, SessionBackend
from fastapi_sessions.typings import SessionInfo

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
    
    async def __call__(self, request: Request) -> Optional[SessionInfo]:
        api_key = request.cookies.get(self.model.name)
        if not api_key:
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
        except:
            if self.auto_error:
                raise HTTPException(
                    status_code=403,
                    detail="Not authenticated"
                )
            else:
                return None

        session_data = await self.backend.read(session_id)
        if not session_data:
            if self.auto_error:
                raise HTTPException(
                    status_code=403,
                    detail="Not authenticated"
                )
            else:
                return None
        
        return session_data, session_id
    
    async def start_and_set_session(self, data: Type[BaseModel], prev_session_info: Optional[SessionInfo], response: Response) -> None:
        if type(data) is not self.data_model:
            raise TypeError("Data is not of right type")
        
        await delete_session(SessionInfo)
        
        signed_encoded_id = self.create_session(data)
        create_client_cookie(signed_encoded_id, response)

    async def create_session(self, data):
        self.delete_session(session_info)

        session_id = self.signer.sign(await self.backend.write(data))
        return b64encode(session_id).decode('utf-8')
        
    def create_client_cookie(self, session_id: str, response: Response):
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

    def delete_client_cookie(self, response: Response):
        response.delete_cookie(self.model.name)

    async def delete_session(self, session_info: Optional[SessionInfo]):
        if session_info is not None:
            await delete_session(session_info[1])

    async def end_and_delete_session(self, session_info: Optional[SessionInfo], response: Response):
        self.delete_client_cookie()
        await self.delete_session(session_info)

test_app = FastAPI()

class SessionInfo(BaseModel):
    id: str
    data: Any