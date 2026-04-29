from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    role: str = Field(description="'learner' or 'tutor'")
    text: str


class LLMRequest(BaseModel):
    transcript: str = Field(default="")
    learner_level: str = "grade6"
    lesson_topic: str = ""
    history: list[HistoryItem] = Field(default_factory=list)


class LLMResponse(BaseModel):
    assistant_response: str
    topic_detected: str = ""
    provider: str = "mock"
