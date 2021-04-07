# Placeholder for SessionAPI()
# Create Sessions for native clients (non-browsers) that do not have cookies.
# NOT FOR BROWSERS - Will not have CSRF protections
# https://tools.ietf.org/html/rfc7235#section-5.1.2 <- Private cache http


from pydantic import BaseModel, Field


class APIParams(BaseModel):
    max_age: int = 14
    max_date: DateTime = None


class OpenAPIKeyHeader(BaseModel):
    type_ = Field("apiKey", alias="type")
    in_ = Field("header", alias="in")
    name: str


class SessionAPI:
    def __init__(self, name):
        self.model = OpenAPIKeyHeader(bearerFormat=name)
