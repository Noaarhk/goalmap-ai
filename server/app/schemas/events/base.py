from pydantic import BaseModel


class TokenEventData(BaseModel):
    text: str
    run_id: str | None = None


class StatusEventData(BaseModel):
    message: str
    node: str


class ErrorEventData(BaseModel):
    code: str
    message: str
