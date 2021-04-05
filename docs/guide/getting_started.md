# Getting started

## Install FastAPI Sessions

The first step is to make sure you have FastAPI installed, along with Uvicorn for testing your API. If this sounds unfamiliar to you, first check out the [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/)

Assuming you have your environment ready, all you need to do is run the code below.

```python
pip install fastapi-sessions
```

## Basic Usage

Getting up and running with FastAPI Sessions is extremely simple. There are three main components you need:

1. Session Data - A pydantic model that specifies what data will be behind a session (e.g. username)
2. `SessionBackend` Class - Where the session data is actually being stored.
3. `SessionCookie` Class - The heavy lifter, it handles all the processing of the sessions

Now lets take a quick look at a quick API. More details on configurations and design choices will be covered later.

---

### Session Data

Its as simple as creating a pydantic model. No catches!

```python
from pydantic import BaseModel

class SessionData(BaseModel):
    username: str
```

---

### Session Backend

We will use the simple `InMemoryBackend()` right now. It stores session data in the server's memory. There are more options that we will go into in the [backend](../backends) section.

```python
from fastapi_sessions.backends import InMemoryBackend

backend = InMemoryDB()
```

---

### Session Cookie

Now we are ready to create our session cookie. It is extremely simple. Just give it a name, a secret key, and pass in our specified data model and backend. Also set `auto_error=False`, what that does will be explained in the [cookies](../cookies) section. Now we are ready to authenticate!

```python
from fastapi_sessions import SessionCookie

session = SessionCookie(
    name="session",
    secret_key="secret",
    data_model=SessionData,
    backend=InMemoryBackend(),
    auto_error=False
)
```

---

### Using Sessions

Now it is as simple as using FastAPI's [dependency injection](https://fastapi.tiangolo.com/tutorial/dependencies/) system to protect your routes! Furthermore FastAPI Sessions is compatible with the OpenAPI specs so it will show up in your docs as authenticated routes.

```python
from typing import Tuple, Optional, Any
from fastapi import FastAPI, Depends, Response, HTTPException

from fastapi_sessions import SessionInfo

test_app = FastAPI()

@test_app.get("/secure")
async def secure_thing(session_data: Optional[SessionInfo] = Depends(test_session)):
    if session_data is None:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated"
        )
    return {"message": "You are secure!"}
```

To create a session (e.g. login), just call `session.create_session(user, response)` and your user has a session.

```python
@test_app.post("/get_session")
async def login(username: str, response: Response, session_info: Optional[SessionInfo] = Depends(test_session)):
    test_user = SessionData(username=username)
    await session.create_session(test_user, response)
    return {"message": "You now have a session!"}
```

To end a session (e.g. logout), just call `session.end_session(session_id, response)` and the session is over.

```python
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

## Putting it all together

Now lets put it all back together to see our session based authentication app.

!!! Warning
    While FastAPI-Sessions makes creating session based authentication easy, it is still a lower level library that lets you make design decisions with security implications.
    Please read through all the docs, especially [Sessions](../../sessions) (forthcoming), and do your own research if you have not worked with cookies and sessions for authentication before.

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