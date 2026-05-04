from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    role: str = Field(description="'learner' or 'tutor'")
    text: str


class StudentContext(BaseModel):
    learning_style: str = "balanced"
    difficulty_level: str = "medium"
    strengths: str = "[]"
    weaknesses: str = "[]"
    recent_summaries: list[str] = Field(default_factory=list)


class LLMRequest(BaseModel):
    transcript: str = Field(default="")
    learner_level: str = "grade6"
    lesson_topic: str = ""
    history: list[HistoryItem] = Field(default_factory=list)
    context_chunks: list[str] = Field(default_factory=list, description="RAG knowledge chunks")
    student_context: StudentContext | None = None


class LLMResponse(BaseModel):
    assistant_response: str
    topic_detected: str = ""
    provider: str = "mock"


class SummarizeRequest(BaseModel):
    session_turns: list[HistoryItem] = Field(default_factory=list)
    lesson_topic: str = ""


class SummarizeResponse(BaseModel):
    summary: str
    topics_covered: str = ""
    mistakes_made: str = ""
    mastery_score: float = 0.0
