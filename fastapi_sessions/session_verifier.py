"""Generic verification code."""
from abc import abstractmethod
from typing import Generic, Union

from fastapi import HTTPException, Request

from fastapi_sessions.backends.session_backend import (
    BackendError,
    SessionBackend,
    SessionModel,
)
from fastapi_sessions.frontends.session_frontend import ID, FrontendError


class SessionVerifier(Generic[ID, SessionModel]):
    @property
    @abstractmethod
    def identifier(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def backend(self) -> SessionBackend[ID, SessionModel]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def auto_error(self) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def auth_http_exception(self) -> HTTPException:
        raise NotImplementedError()

    @abstractmethod
    def verify_session(self, model: SessionModel) -> bool:
        raise NotImplementedError()

    async def __call__(self, request: Request):
        try:
            session_id: Union[ID, FrontendError] = request.state.session_ids[
                self.identifier
            ]
        except Exception:
            if self.auto_error:
                raise HTTPException(
                    status_code=500, detail="internal failure of session verification"
                )
            else:
                return BackendError(
                    "failed to extract the {} session from state", self.identifier
                )

        if isinstance(session_id, FrontendError):
            if self.auto_error:
                raise self.auth_http_exception
            return

        session_data = await self.backend.read(session_id)
        if not session_data or not self.verify_session(session_data):
            if self.auto_error:
                raise self.auth_http_exception
            return

        return session_data
