# Example

To document

```python
from typing import Tuple, Optional, Any

from pydantic import BaseModel
from fastapi import FastAPI, Depends, Response, HTTPException

from fastapi_sessions import SessionCookie, SessionInfo
from fastapi_sessions.backends import InMemoryBackend

test_app = FastAPI()

class SessionData(BaseModel):
    username: str


class BadSessionData(BaseModel):
    fakename: str


test_session = SessionCookie(
    name="session",
    secret_key="helloworld",
    backend=InMemoryBackend(),
    data_model=SessionData,
    scheme_name="Test Cookies",
    auto_error=False
)


@test_app.get("/secure")
async def secure_thing(session_data: Optional[SessionInfo] = Depends(test_session)):
    if session_data is None:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated"
        )
    return {"message": "You are secure", "user": session_data}

@test_app.post("/get_session")
async def login(username: str, response: Response, session_info: Optional[SessionInfo] = Depends(test_session)):
    old_session = None
    if session_info:
        old_session = session_info[0]
    
    test_user = SessionData(username=username)
    await test_session.create_session(test_user, response, old_session)
    return {"message": "You now have a session", "user": test_user}

@test_app.post("/leave_session")
async def logout(response: Response, session_info: Optional[SessionInfo]  = Depends(test_session)):
    if not session_info:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated"
        )
    await test_session.end_session(session_info[0], response)
    return {"message": "You now don't have a session", "user": session_info}
```