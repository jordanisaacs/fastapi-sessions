# FastAPI-Sessions


---

Documentation: [https://jordanisaacs.github.io/fastapi-sessions/](https://jordanisaacs.github.io/fastapi-sessions/)

Source Code: [https://github.com/jordanisaacs/fastapi-sessions/](https://github.com/jordanisaacs/fastapi-sessions/)

PyPI: [https://pypi.org/project/fastapi-sessions/](https://pypi.org/project/fastapi-sessions/)

---

Quickly add session authentication to your FastAPI project. **FastAPI Sessions** is designed to be user friendly and customizable.


## Features

- [x] Dependency injection to protect routes
- [x] Compatible with FastAPI's auto generated docs
- [x] Pydantic models for verifying session data
- [x] Abstract session backend so you can build one that fits your needs
- [x] Abstract frontends to choose how you extract the session ids (cookies, header, etc.)
- [x] Create verifiers based on the session data
- [x] Mix and match frontends and backends

Currently Included Backends/Frontends:

- [x] Backends
    - [x] In memory dictionary
- [x] Frontends
    - [x] Signed cookies


Upcoming:

* Documentation and user guides
* More backends and frontends

## Installation

```python
pip install fastapi-sessions
```

## Getting Started

Check out the guide to using fastapi-sessions: [https://jordanisaacs.github.io/fastapi-sessions/guide/getting_started/](https://jordanisaacs.github.io/fastapi-sessions/guide/getting_started/)
