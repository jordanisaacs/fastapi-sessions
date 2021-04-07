"""
Class and functions to create a session's csrf_token and session_id.

Classes:
    SessionDataWrapper

Functions:
    generate_token() -> str
"""

from os import urandom
from base64 import b64encode
from typing import TypeVar, Generic, Optional

from pydantic.generics import GenericModel
from pydantic import Field, BaseModel

SessionData = TypeVar("SessionData", bound=BaseModel)


def generate_token() -> str:
    """Generate a CSRN and return it in string form.

    Returns:
        str: base 64 encoded 64 random bytes as a string
    """
    return b64encode(urandom(64)).decode("utf-8")


class SessionDataWrapper(GenericModel, Generic[SessionData]):
    data: SessionData
    csrf_token: Optional[str] = Field(default_factory=generate_token)
    session_id: str = Field(default_factory=generate_token)