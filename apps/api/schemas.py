from datetime import datetime
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    learner_id: str = Field(min_length=1, max_length=100)
    lesson_topic: str = Field(min_length=1, max_length=200)


class SessionResponse(BaseModel):
    session_id: str
    learner_id: str
    lesson_topic: str
    created_at: datetime
    status: str


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


class TurnRequest(BaseModel):
    text_input: str = Field(default="", max_length=2000)


class TurnResponse(BaseModel):
    session_id: str
    transcript: str
    assistant_response: str
    audio_url: str
    response_ms: int


class TurnHistoryItem(BaseModel):
    transcript: str
    assistant_response: str
    created_at: datetime


class ProgressResponse(BaseModel):
    learner_id: str
    total_sessions: int
    total_turns: int
    avg_latency_ms: int
    topics_studied: list[str]
    recent_sessions: list[SessionResponse]


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=120)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
