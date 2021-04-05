from typing import TypeVar, Generic

from pydantic.generics import GenericModel
from pydantic import Field

from os import urandom
from base64 import b64encode

SessionData = TypeVar("SessionData")


def generate_token() -> str:
    """ Generate a new CSPRNG """
    return b64encode(urandom(64)).decode("utf-8")   


class SessionDataWrapper(GenericModel, Generic[SessionData]):
    data: SessionData
    csrf_token: str = Field(default_factory=generate_token)
    session_id: str = Field(default_factory=generate_token)
