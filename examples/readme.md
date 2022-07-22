## Run tests

```bash
pip install fastapi itsdangerous pydantic uvicorn
uvicorn basic:app --reload
uvicorn basic_redis:app --reload
```