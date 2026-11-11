"""Pydantic request/response schemas (API boundary)."""

from datetime import datetime

from pydantic import BaseModel, Field


# ----- Auth -----


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=4, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ----- AI Config -----


class AiConfigUpdate(BaseModel):
    base_url: str = Field(min_length=1, max_length=512)
    model: str = Field(min_length=1, max_length=128)
    # Omit or empty to leave unchanged when updating; send "" explicitly to clear
    api_key: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class AiConfigOut(BaseModel):
    base_url: str
    model: str
    temperature: float
    # Never expose the raw key — only whether one is stored
    has_api_key: bool
    updated_at: datetime | None = None


# ----- Chat -----


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    # Optional: continue an existing session; omit to open/reuse active Spanish session
    session_id: int | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    text: str
    display_text: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: int
    language: str
    started_at: datetime
    ended_at: datetime | None = None
    summary: str | None = None
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    session_id: int
    user_message: MessageOut
    assistant_message: MessageOut
    # True when reply came from the local stub (no LLM / unreachable)
    mocked: bool = False
