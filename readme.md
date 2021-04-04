# FastAPI-Sessions

## Ready-to-use cookie based sessions with custom backends for FastAPI

Usage
More info coming.
```python
class SessionData(BaseModel):
    username: str

test_session = SessionCookie(
    name="session",
    secret_key="helloworld",
    data_model=SessionData,
    backend=InMemoryBackend(),
    scheme_name="Test Cookies",
    auto_error=False
)

@test_app.get("/secure")
async def secure_thing(session: Tuple[SessionData, str] = Depends(test_session)):
    if session is None:
        raise HTTPException(
            status_code=403,
            detail="Not authenticated"
        )
    return {"message": "You are secure", "user": session[0]}

@test_app.post("/get_session")
async def login(username: str, response: Response):
    test_user = SessionData(username=username)
    await test_session.start_and_set_session(test_user, response)
    return {"message": "You now have a session", "user": test_user}

@test_app.post("/leave_session")
async def logout(response: Response, session: Optional[Tuple[SessionData, str]] = Depends(test_session)):
    await test_session.end_and_delete_session(session, response)
    return {"message": "You now don't have a session", "user": session}
```
