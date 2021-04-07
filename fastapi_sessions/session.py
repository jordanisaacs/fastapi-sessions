# Placeholder for Session()
# Will wrap both SessionCookie() and SessionAPI()
# Allow for Cookies and API to have the same backend

from fastapi_sessions.authentication.session_wrapper import (
    SessionDataWrapper,
    SessionData,
)
from itsdangerous import URLSafeTimedSerializer

from typing import Optional, Union, Tuple, Type, Generic

from pydantic import BaseModel

from fastapi_sessions.backends.session_backend import SessionBackend
from fastapi_sessions.authentication.session_api import SessionAPI, APIParams
from fastapi_sessions.authentication.session_cookie import (
    SessionCookie,
    CookieParameters,
    SessionCookieError,
)

from fastapi import Request, Response, HTTPException


class Session(Generic[SessionData]):
    def __init__(
        self,
        name: str,
        secret_key: str,
        data_model: Type[SessionData],
        backend: SessionBackend,
        cookie_params: Optional[CookieParameters] = None,
        copy_cookie_params: bool = True,
        api_params: Optional[APIParams] = None,
        scheme_name: Optional[str] = None,
        auto_error: bool = False,
    ):
        # self.model = ??? OpenAPI docs are broken currently
        self.name = name
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

        self.signer = URLSafeTimedSerializer(secret_key, salt=name)
        self.backend = backend
        self.data_model = data_model

        self._cookie: Optional[SessionCookie] = None
        if cookie_params is not None:
            if copy_cookie_params is True:
                cookie_params = cookie_params.copy()
            self.cookie = SessionCookie(
                name=name,
                cookie_params=cookie_params,
            )

        self.api: Optional[SessionAPI] = None
        # if api_params is not None:
        #     self.cookie = SessionAPI()

    def set_cookie_params(
        self, cookie_params: CookieParameters, copy: bool = True
    ) -> None:
        """Set the parameters of the SessionCookie.
        Creates new SessionCookie if doesn't exist.

        New parameters do not carry over to existing cookies.
        `max_age` will affect existing cookies serverside because of timestamp signing.

        Args:
            cookie_params (CookieParameters): The new cookie parameters
            copy (bool, optional): Copy the cookie_params.
            If false then will alias. Defaults to True.
        """
        if copy:
            cookie_params = cookie_params.copy()

        if not self.cookie:
            self.cookie = SessionCookie(
                name=self.name,
                cookie_params=cookie_params,
            )
        else:
            self.cookie.params = cookie_params

    # async def delete_session_cookie(self):
    #     """Deletes the SessionCookie.

    #     To reduce unnecessary storage also deletes
    #     all existing sessions based on cookies.

    #     Existing cookies on the client can't be deleted but
    #     will be invalid as the cookie cannot authenticate and the backend
    #     won't have the corresponding data to validate.
    #     """
    #     await self.backend.remove_sessions(cookie=True)
    #     self.cookie = None

    # async def delete_sessions(cookie=False, api=False):
    #     await self.backend.remove_sessions(cookie=cookie, api=api)

    async def end_cookie_session(
        self, session_id: str, response: Optional[Response] = None
    ):
        if response:
            self.cookie.delete_session(response)
        await self.backend.remove(session_id)

    async def create_cookie_session(
        self,
        session_id: str,
        session_data: SessionData,
        response: Response,
        prev_session_id: Optional[str] = None,
    ) -> str:
        if not self.cookie:
            raise ValueError("There is no SessionCookie set")

        if prev_session_id:
            await self.backend.remove(prev_session_id)

        data = SessionDataWrapper[SessionData](data=session_data)

        if data.csrf_token is None:
            raise ValueError("CSRF token was not generated")

        self.cookie.create_session(
            data.session_id, data.csrf_token, self.signer, response
        )

        return data.session_id

    async def __call__(
        self, request: Request
    ) -> Union[Tuple[str, BaseModel], SessionCookieError]:
        if self.cookie:
            cookie_result = self.try_retrieve_cookie_id(request)

            if (
                cookie_result != SessionCookieError.NotSessionCookie
                and type(cookie_result) is SessionCookieError
            ):
                return cookie_result
            elif type(cookie_result) is Tuple[str, str]:
                session_id = cookie_result[0]
                csrf_token = cookie_result[1]
                await self.verify_cookie(session_id, csrf_token)

        raise NotImplementedError("SessionAPI not implemented")
        # result = self.retrieve_id(request)
        # if result is not str:
        #    return result

        # session_data = await self.backend.read(session_id=result)

        # result = self.api.retrieve_and_unsign_session(request, self.signer)

    def try_retrieve_cookie_id(
        self, request: Request
    ) -> Union[Tuple[str, str], SessionCookieError]:
        session_id, csrf_or_error = self.cookie.retrieve_and_unsign_session(
            request, self.signer
        )

        if csrf_or_error is SessionCookieError.NotSessionCookie:
            return csrf_or_error
        elif session_id is str and csrf_or_error is str:
            return session_id
        elif session_id is str and csrf_or_error in [
            SessionCookieError.MissingCSRFCookie,
            SessionCookieError.CSRFCorrupted,
            SessionCookieError.CSRFExpired,
        ]:
            # Has a potential session and a problem with the CSRF token
            # a potential attack, delete session if exists
            await self.backend.remove(session_id)
            return self.authentication_error(csrf_or_error)
        else:
            assert csrf_or_error is SessionCookieError
            return self.authentication_error(csrf_or_error)

    async def verify_cookie(
        self, session_id: str, csrf_token: str
    ) -> Union[Tuple[str, BaseModel], SessionCookieError]:
        session_data = await self.backend.read(session_id, self.data_model)
        if not session_data:
            return self.authentication_error(SessionCookieError.InvalidSession)

        # Invalid CSRF, a potential CSRF attack. Delete session
        if csrf_token != session_data.csrf_token:
            await self.backend.remove(session_id)
            return self.authentication_error(SessionCookieError.InvalidCSRF)

        return session_id, session_data.data

    def authentication_error(self, error: SessionCookieError) -> SessionCookieError:
        if self.auto_error:
            raise HTTPException(status_code=403, detail=error)
        return error
