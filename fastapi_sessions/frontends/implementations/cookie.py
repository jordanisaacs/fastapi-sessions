from enum import Enum
from typing import Optional, Union
from uuid import UUID

from fastapi import HTTPException, Response
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase
from fastapi_sessions.frontends.session_frontend import FrontendError, SessionFrontend
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic.main import BaseModel
from starlette.requests import Request


class SameSiteEnum(str, Enum):
    lax = "lax"
    strict = "strict"
    none = "none"


class CookieParameters(BaseModel):
    max_age: int = 14 * 24 * 60 * 60  # 14 days in seconds
    path: str = "/"
    domain: Optional[str] = None
    secure: bool = False
    httponly: bool = True
    samesite: SameSiteEnum = SameSiteEnum.lax


class SessionCookie(SecurityBase, SessionFrontend[UUID]):
    def __init__(
        self,
        *,
        cookie_name: str,
        identifier: str,
        secret_key: str,
        cookie_params: CookieParameters,
        scheme_name: Optional[str] = None,
        auto_error: bool = False
    ):
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.cookie},
            name=cookie_name,
        )
        self._identifier = identifier
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error
        self.signer = URLSafeTimedSerializer(secret_key, salt=cookie_name)
        self.cookie_params = cookie_params.model_copy(deep=True)

    @property
    def identifier(self) -> str:
        return self._identifier

    def __call__(self, request: Request) -> Union[UUID, FrontendError]:
        # Get the signed session id from the session cookie

        signed_session_id = request.cookies.get(self.model.name)

        if not signed_session_id:
            if self.auto_error:
                raise HTTPException(status_code=403, detail="No session provided")

            error = FrontendError("No session cookie attached to request")
            super().attach_id_state(request, error)
            return error

        # Verify and timestamp the signed session id
        try:
            session_id = UUID(
                self.signer.loads(
                    signed_session_id,
                    max_age=self.cookie_params.max_age,
                    return_timestamp=False,
                )
            )
        except (SignatureExpired, BadSignature):
            if self.auto_error:
                raise HTTPException(status_code=401, detail="Invalid session provided")
            error = FrontendError("Session cookie has invalid signature")
            super().attach_id_state(request, error)
            return error

        super().attach_id_state(request, session_id)
        return session_id

    def delete_from_response(self, response: Response) -> None:
        if self.cookie_params.domain:
            response.delete_cookie(
                key=self.model.name,
                path=self.cookie_params.path,
                domain=self.cookie_params.domain,
            )
        else:
            response.delete_cookie(key=self.model.name, path=self.cookie_params.path)

    def attach_to_response(self, response: Response, session_id: UUID) -> None:
        response.set_cookie(
            key=self.model.name,
            value=str(self.signer.dumps(session_id.hex)),
            **dict(self.cookie_params),
        )
