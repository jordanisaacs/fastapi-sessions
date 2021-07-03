# FastAPI-Sessions



---

Documentation: [https://jordanisaacs.github.io/fastapi-sessions/](https://jordanisaacs.github.io/fastapi-sessions/)

Source Code: [https://github.com/jordanisaacs/fastapi-sessions/](https://github.com/jordanisaacs/fastapi-sessions/)

---

Note: Currently in the middle of a [rewrite](https://github.com/jordanisaacs/fastapi-sessions/issues/7#issue-931170265) to bring library to a stable point and bring some needed features

Quickly add session authentication to your FastAPI project. **FastAPI Sessions** is designed to be user friendly and customizable.


## Features

- [x] Dependency injection to protect the routes you want
- [x] Timestamp signed session IDs with [itsdangerous](https://itsdangerous.palletsprojects.com/en/1.1.x/)
- [x] Compabitibility with OpenAPI docs using [APIKeyCookie](https://swagger.io/docs/specification/authentication/cookie-authentication/)
- [x] Pydantic models for verifying session data
- [x] Abstract session backend so you can build one that fits your needs
- [x] Currently included backends
    - [x] In memory


Upcoming:

* Documentation and user guides
* More backends!

> This project was started on April 3rd and progress is ongoing. Follow the repo for updates!

## Installation

```py
pip install fastapi-sessions
```

## Guide

Check out the guide to building and using session based authentication with fastapi-sessions: [https://jordanisaacs.github.io/fastapi-sessions/guide/getting_started/](https://jordanisaacs.github.io/fastapi-sessions/guide/getting_started/)
