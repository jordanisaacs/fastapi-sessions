from typing import Type, Optional, Generic, TypeVar
from datetime import datetime

from base64 import b64encode, b64decode

from fastapi import Request, HTTPException, Response
from fastapi.security.api_key import APIKeyBase, APIKey, APIKeyIn

from itsdangerous import URLSafeSerializer
from itsdangerous.exc import BadTimeSignature, SignatureExpired

from pydantic import BaseModel
from pydantic.generics import GenericModel

from fastapi_sessions.backends import SessionBackend
from fastapi_sessions.typings import SessionInfo


class SessionCookie(APIKeyBase):
    SessionData = TypeVar["SessionData"]

    class SessionDataWrapper(GenericModel, Generic[SessionData]):
        csrf_token: str

    def __init__(
        self,
        *,
        name: str,
        secret_key: str,
        data_model: Type[BaseModel],
        backend: Type[SessionBackend],
        scheme_name: Optional[str] = None,
        auto_error: bool = True,
        max_age: int = 14 * 24 * 60 * 60,  # 14 days in seconds
        expires: datetime = None,
        path: str = "/",
        domain: str = None,
        secure: bool = True,
        httponly: bool = True,
        samesite: str = "strict",
    ):
        self.model: APIKey = APIKey(**{"in": APIKeyIn.cookie}, name=name)
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

        self.signer = URLSafeSerializer(secret_key, salt=name)
        self.backend = backend
        self.data_model = data_model

        self.max_age = max_age
        self.expires = expires
        self.path = path
        self.domain = domain
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite

    async def __call__(self, request: Request) -> Optional[SessionInfo]:
        # Get the signed session id from the session cookie
        signed_session_id = request.cookies.get(self.model.name)
        if not signed_session_id:
            return self.authentication_error()

        # Verify and timestamp the signed session id
        try:
            session_id = self.signer.loads(
                signed_session_id,
                max_age=self.max_age,
                return_timestamp=False,
            ).decode("utf-8")
        except (SignatureExpired, BadTimeSignature):
            return self.authentication_error()

        # Attempt to read the corresponding session data from the backend
        session_data = await self.backend.read(session_id)
        if not session_data:
            return self.authentication_error()

        # Retrieve the csrf token, if it doesn't exist then its a potential
        # csrf attack and remove the session
        frontend_signed_csrf_token = self.get_csrf_token(request)
        if not frontend_signed_csrf_token:
            await self.backend.remove(session_id)
            return self.authentication_error()

        # Validate the csrf token, if not valid then its a potential csrf
        # attack and delete the session
        backend_csrf_token = session_data["csrf_token"]
        try:
            frontend_csrf_token = self.signer.loads(
                frontend_signed_csrf_token,
                max_age=self.max_age,
                return_timestamp=False,
            ).decode("utf-8")
            assert frontend_csrf_token == backend_csrf_token
        except (SignatureExpired, BadTimeSignature, AssertionError):
            await self.backend.remove(session_id)
            return self.authentication_error()

        del session_data["csrf_token"]

        return self.model(**session_data), session_id

    def authentication_error(self):
        if self.auto_error:
            raise HTTPException(status_code=403, detail="Not authenticated")
        else:
            return None

    # To implement
    async def get_csrf_token(
        self, request: Request, signed_backend_csrf_token: str
    ) -> Optional[str]:
        return frontend_signed_csrf_token

    async def start_and_set_session(
        self,
        data: Type[BaseModel],
        prev_session_info: Optional[SessionInfo],
        response: Response,
    ) -> None:
        if type(data) is not self.data_model:
            raise TypeError("Data is not of right type")

        if prev_session_info is not None:
            await self.backend.remove(prev_session_info[1])

        session_id, csrf_token = await self.backend.write(data.dict())

        response.set_cookie(
            key=self.model.name,
            value=session_id,
            max_age=self.max_age.total_seconds(),
            expires=self.expires,
            path=self.path,
            domain=self.domain,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite,
        )

    async def remove_and_delete_session(
        self,
        session_info: Optional[SessionInfo],
        response: Response,
    ):
        response.delete_cookie(self.model.name)

        if session_info is not None:
            await self.backend.remove(session_info[1])
