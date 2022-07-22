## Run tests

```bash
pip install fastapi itsdangerous pydantic redis uvicorn
uvicorn basic:app --reload
uvicorn basic_redis:app --reload
```