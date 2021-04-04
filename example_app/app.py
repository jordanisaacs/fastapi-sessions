from typing import Tuple, Optional, Any
from fastapi_sessions import SessionCookie
from fastapi_sessions.backends import SessionBackend, InMemoryBackend
from fastapi_sessions.typings import SessionInfo

from pydantic import BaseModel
from fastapi import FastAPI, Depends, Response, HTTPException

test_app = FastAPI()

class SessionData(BaseModel):
    username: str

class Message(BaseModel):
    detail = str

test_session = SessionCookie(
    name="session",
    secret_key="helloworld",
    data_model=SessionData,
    backend=InMemoryBackend(),
    scheme_name="Test Cookies",
    auto_error=False
)

@test_app.get("/secure", responses={403: {"model": Any}})
async def secure_thing(session_data: Optional[SessionInfo] = Depends(test_session)):
    if session_data is None:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated"
        )
    return {"message": "You are secure", "user": session[0]}

@test_app.post("/get_session")
async def login(username: str, response: Response, session_info: Optional[SessionInfo] = Depends(test_session)):
    test_user = SessionData(username=username)
    await test_session.start_and_set_session(test_user, response)
    return {"message": "You now have a session", "user": test_user}

@test_app.post("/leave_session")
async def logout(response: Response, session_info: Optional[SessionInfo]  = Depends(test_session)):
    await test_session.end_and_delete_session(session_info, response)
    return {"message": "You now don't have a session", "user": session_info}