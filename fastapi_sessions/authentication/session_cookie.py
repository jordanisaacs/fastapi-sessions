from datetime import datetime
from enum import Enum
from typing import Optional, Tuple, Union

from pydantic import BaseModel, Field
from fastapi import Request, Response

from itsdangerous import (
    URLSafeTimedSerializer,
    SignatureExpired,
    BadTimeSignature,
)


class SessionCookieError(Enum):
    NotSessionCookie = 1
    MissingCSRFCookie = 2
    MissingSessionCookie = 3
    SessionExpired = 4
    SessionCorrupted = 5
    CSRFExpired = 6
    CSRFCorrupted = 7
    InvalidSession = 8
    InvalidCSRF = 9


class OpenAPIKeyCookie(BaseModel):
    type_ = Field("apiKey", alias="type")
    in_ = Field("cookie", alias="in")
    name: str


class OpenAPIKeyHeader(BaseModel):
    type_ = Field("apiKey", alias="type")
    in_ = Field("cookie", alias="in")
    name: str


class CookieParameters(BaseModel):
    max_age: int = 14 * 24 * 60 * 60  # 14 days in seconds
    expires: Optional[datetime] = None
    path: str = "/"
    domain: Optional[str] = None
    secure: bool = False
    httponly: bool = True
    samesite: str = "lax"


class SessionCookie:
    def __init__(
        self,
        *,
        name: str,
        cookie_params: CookieParameters,
    ) -> None:
        self.name = name
        self.params = cookie_params

    def create_session(
        self,
        session_id: str,
        csrf_token: str,
        signer: URLSafeTimedSerializer,
        response: Response,
    ) -> None:
        response.set_cookie(
            key=self.name,
            value=signer.dumps(session_id, salt=self.get_session_name()),
            **self.params.dict(),
        )

        response.headers[self.get_csrf_header_name()] = signer.dumps(
            csrf_token, salt=self.get_csrf_name()
        )

    def delete_session(self, response: Response) -> None:
        response.delete_cookie(self.name)

    async def retrieve_and_unsign_session(
        self, request: Request, signer: URLSafeTimedSerializer
    ) -> Tuple[Optional[str], Union[str, SessionCookieError]]:
        """Attempt to retrieve and unsign the csrf and session_id."""
        # Retrieve the signed csrf token
        signed_csrf_token = await self.get_csrf_token(request)

        # Get the signed session id from the session cookie
        signed_session_id = request.cookies.get(self.name)
        if not signed_session_id:
            if signed_csrf_token:
                return None, SessionCookieError.MissingSessionCookie
            return None, SessionCookieError.NotSessionCookie

        # Unsign and timestamp the signed session id
        try:
            session_id = signer.loads(
                signed_session_id,
                max_age=self.params.max_age,
                return_timestamp=False,
            )
        except SignatureExpired:
            return None, SessionCookieError.SessionExpired
        except BadTimeSignature:
            return None, SessionCookieError.SessionCorrupted

        if not signed_csrf_token:
            # Missing CSRF token, but has a session cookie,
            # a potential CSRF attack
            return session_id, SessionCookieError.MissingCSRFCookie

        # Unsign and timestamp the signed CSRF token
        try:
            csrf_token = signer.loads(
                signed_csrf_token,
                max_age=self.params.max_age,
                return_timestamp=False,
            )
        except SignatureExpired:
            return session_id, SessionCookieError.CSRFExpired
        except BadTimeSignature:
            return session_id, SessionCookieError.CSRFCorrupted

        return session_id, csrf_token

    async def get_csrf_token(self, request: Request) -> Optional[str]:
        # First try and get it from an html form !!! Not activating. needs more research
        form = await request.form()
        print(form)
        # signed_csrf_token = form.get(self.get_csrf_form_name())
        # if signed_csrf_token:
        #     return signed_csrf_token

        # Next try and get it from the header
        signed_csrf_token = request.headers.get(self.get_csrf_header_name())
        print(request.headers)
        return signed_csrf_token

    def get_csrf_header_name(self) -> str:
        return "X-" + self.name.replace("_", "-").upper() + "-csrf"

    def get_csrf_name(self) -> str:
        return self.name + "_csrf"

    def get_session_name(self) -> str:
        return self.name + "_cookie"


# async def end_session(self, session_id: str, response: Response):
#     response.delete_cookie(self.model.name)
#     await self.backend.remove(session_id)
