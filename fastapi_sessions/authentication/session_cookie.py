from datetime import datetime
from typing import Optional, Type, NewType, Tuple, Dict, Any

from pydantic import BaseModel
from fastapi import Request, HTTPException, Response
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

from fastapi_sessions.backends.session_backend import SessionBackend
from fastapi_sessions.authentication.session_wrapper import SessionDataWrapper

SessionInfo = NewType("SessionInfo", Tuple[str, Dict[str, Any]])


class SessionCookie(SecurityBase):
    def __init__(
        self,
        *,
        name: str,
        secret_key: str,
        backend: Type[SessionBackend],
        data_model: Type[BaseModel],
        scheme_name: Optional[str] = None,
        auto_error: bool = True,
        max_age: int = 14 * 24 * 60 * 60,  # 14 days in seconds
        expires: Optional[datetime] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = True,
        samesite: str = "lax",
    ):
        self.model: APIKey = APIKey(**{"in": APIKeyIn.cookie}, name=name)
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

        self.signer = URLSafeTimedSerializer(secret_key, salt=name)
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
        """Authenticate a request."""
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
            )
        except (SignatureExpired, BadTimeSignature):
            return self.authentication_error()

        # Attempt to read the corresponding session data from the backend
        session_data = await self.backend.read(session_id)
        if not session_data:
            return self.authentication_error()
        session_data = SessionDataWrapper[self.data_model](
            session_id=session_id,
            **session_data,
        )

        # Retrieve the csrf token, if it doesn't exist then its a potential
        # csrf attack and remove the session
        frontend_signed_csrf_token = request.cookies.get(self.model.name + "csrf")
        if not frontend_signed_csrf_token:
            await self.backend.remove(session_id)
            return self.authentication_error()

        # Validate the csrf token, if not valid then its a potential csrf
        # attack and delete the session
        try:
            frontend_csrf_token = self.signer.loads(
                frontend_signed_csrf_token,
                max_age=self.max_age,
                return_timestamp=False,
            )
            assert frontend_csrf_token == session_data.csrf_token
        except (SignatureExpired, BadTimeSignature, AssertionError):
            await self.backend.remove(session_id)
            return self.authentication_error()

        return session_data.session_id, session_data.data

    def authentication_error(self) -> None:
        """Generate an authentication error if self.auto_error is True.

        Raises:
            HTTPException: 403, not authenticated
        """
        if self.auto_error:
            raise HTTPException(status_code=403, detail="Not authenticated")

    async def create_session(
        self,
        data: Type[BaseModel],
        response: Response,
        prev_session_info: Optional[str] = None,
    ):
        session_data = SessionDataWrapper[self.data_model](data=data)
        if prev_session_info:
            await self.backend.remove(prev_session_info)

        await self.backend.write(session_data)

        response.set_cookie(
            key=self.model.name,
            value=self.signer.dumps(session_data.session_id),
            max_age=self.max_age,
            expires=self.expires,
            path=self.path,
            domain=self.domain,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite,
        )

        # Temporary csrf cookie setting
        response.set_cookie(
            key=self.model.name + "csrf",
            value=self.signer.dumps(session_data.csrf_token),
        )

    async def end_session(self, session_id: str, response: Response):
        response.delete_cookie(self.model.name)
        await self.backend.remove(session_id)
