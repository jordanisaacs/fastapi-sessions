from pydantic import BaseModel
from fastapi_sessions.session_wrapper import SessionData, SessionDataWrapper
from typing import Type
import pytest


class BadSessionClass:
    def __init__(self, name: str):
        self.name = name


class GoodSessionClass(BaseModel):
    name: str


class SubGoodSessionClass(GoodSessionClass):
    id: str


# Arrange


@pytest.fixture
def get_goodsessionclass():
    return GoodSessionClass


@pytest.fixture
def get_badsessionclass():
    return BadSessionClass


@pytest.fixture
def get_subgoodsessionclass():
    return SubGoodSessionClass


@pytest.fixture
def get_badsessiondata():
    return BadSessionClass(name="john")


@pytest.fixture
def get_goodsessiondata():
    data = GoodSessionClass(name="doe")
    return data


@pytest.fixture
def get_subgoodsessiondata(get_goodsessiondata: GoodSessionClass):
    return SubGoodSessionClass(id="123", **get_goodsessionclass.dict())


def test_session_wrapper_pass(get_goodsessionclass, get_subgoodsessiondata):
    SessionDataWrapper[get_goodsessionclass](data=get_subgoodsessiondata)