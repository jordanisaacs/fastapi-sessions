# Getting started

## Install FastAPI Sessions

The first step is to make sure you have FastAPI installed, along with Uvicorn for testing your API. If this sounds unfamiliar to you, first check out the [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/)

Assuming you have your environment ready, lets install the library using pip.

```python
pip install fastapi-sessions
```

## Basic Usage

To get up and running with FastAPI sessions there are three main components you will use.

1. `SessionFrontend` Abstract Class - This class provides the interface for extracting the session IDs from the request whether it is a cookie, header, etc.
1. `SessionBackend` Abstract Class - This class provides the interface for CRUD operations of your session data.
2. `SessionVerifier` Abstract Class - This class is where you verify that the provided session ID is actually valid.

Now lets take a quick look at a quick API. More details on configurations and design choices will be covered later.

---

### Session Data

Its as simple as creating a pydantic model. No catches!

```python
from pydantic import BaseModel

class SessionData(BaseModel):
    username: str
```

### Session Frontend

We will use the provided `SessionCookie` frontend. The cookie's value is the signed UUID that is used as a key to the session data on the backend. Take notice of the `identifier` parameter, it connects the frontend to its corresponding verifier.

```python
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters

cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)

```

---

### Session Backend

We will use the simple `InMemoryBackend[ID, Data]()` right now. It stores session data in the server's memory. As `SessionCookie` utilizes `UUID` that is our ID type.

```python
from uuid import UUID
from fastapi_sessions.backends.implementations import InMemoryBackend

backend = InMemoryBackend[UUID, SessionData]()
```

---

### Session Verifier

With the data, frontend, and backend all set up we now need to write our verifier. We will keep it simple and just have it verify that the session exists in the backend. It is a little unseemly as it utilizes Python's abstract classes. Notice we inerit from `SessionVerifier` which does all the heavy lifting of reading from the backend and obtaining the session from the frontend. The `identifier` must match the corresponding frontend `identifier`.

```python
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi import HTTPException

class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)
```

---

### Bringing it together

Now we utilize FastAPI's [dependency injection](https://fastapi.tiangolo.com/tutorial/dependencies/) system to protect your routes! Furthermore FastAPI Sessions is compatible with the OpenAPI specs so they will show up in your docs as authenticated routes.

#### Create Session Route

Lets start with a simple session creation endpoint. This is not a protected.

```python

from uuid import uuid4
from fastapi import FastAPI, Response

app = FastAPI()

@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):

    session = uuid4()
    data = SessionData(name=name)

    await backend.create(session, data)
    cookie.attach_to_response(response, session)

    return "created session for {name}"
```

Now that our user can create a session, lets verify who they are. Notice how we depend on both the cookie and the verifier. The frontend must always be before the verifier as FastAPI Sessions relies on some [hackery](https://github.com/tiangolo/fastapi/issues/2575). It is to enable frontends and backends to be mixed and matched while still taking advantage of dependency injection and autodocs. The cookie extracts the session id and then the verifier checks the validity of the session.

```python
from fastapi import Depends

@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data
```

To end a session (e.g. logout), just delete it from the backend. As we now require the `session_id` we move it to be a dependency that returns a value. Not all frontends have the option, but with cookies we can delete it in the response which we do.

```python
@app.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"
```

## Putting it all together

Now lets put it all back together to see our session based authentication app.

!!! Warning
    While FastAPI-Sessions makes creating session based authentication easy, there are security implications.
    Please read through all the docs, especially [Sessions](../../sessions) (forthcoming), and do your own research if you have not worked with cookies and sessions for authentication before. 

```python
from pydantic import BaseModel
from fastapi import HTTPException, FastAPI, Response, Depends
from uuid import UUID, uuid4

import sys

sys.path.append("..")

from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters


class SessionData(BaseModel):
    username: str


cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)
backend = InMemoryBackend[UUID, SessionData]()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)

app = FastAPI()


@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):

    session = uuid4()
    data = SessionData(name=name)

    await backend.create(session, data)
    cookie.attach_to_response(response, session)

    return "created session for {name}"


@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data


@app.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"

```