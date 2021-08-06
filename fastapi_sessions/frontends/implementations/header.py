from enum import auto
from typing import Optional
from uuid import UUID

from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.base import SecurityBase
from fastapi_sessions.frontends.session_frontend import FrontendError, SessionFrontend
from itsdangerous.url_safe import URLSafeSerializer, URLSafeTimedSerializer


class SessionHeader(SecurityBase, SessionFrontend[UUID]):
    def __init__(
        self,
        *,
        header_name: str,
        max_age: int,
        identifier: str,
        secret_key: str,
        scheme_name: Optional[str] = None,
        auto_error: bool = False
    ):
        self.model: APIKey = APIKey(**{"in": APIKeyIn.header}, name=header_name)
        self.secret_key = secret_key
        self._identifier = identifier
        self.auto_error = auto_error
        self.signer = URLSafeTimedSerializer(secret_key, salt=header_name)

    @property
    def identifier(self):
        return self._identifier

    def __call__(self, request: Request):
        signed_session_id = request.headers.get(self.model.name)

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
