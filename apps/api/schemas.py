from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["admin", "teacher", "student", "parent"]


class SessionCreateRequest(BaseModel):
    learner_id: str = Field(default="", max_length=150)
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
    audio_base64: str | None = Field(default=None, description="Base64 encoded audio for STT")


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
    email: str
    role: str
    full_name: str = ""


class UserResponse(BaseModel):
    email: str
    role: str
    full_name: str = ""
    grade_level: str | None = None
    is_active: bool = True


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class UserCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=120)
    role: Role
    full_name: str = Field(default="", max_length=150)
    grade_level: str | None = Field(default=None, max_length=50)


class UserUpdateRequest(BaseModel):
    role: Role | None = None
    full_name: str | None = Field(default=None, max_length=150)
    grade_level: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=120)


class ClassCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=500)
    teacher_email: str | None = None


class ClassResponse(BaseModel):
    class_id: str
    name: str
    description: str
    teacher_email: str
    teacher_name: str = ""
    member_count: int = 0
    created_at: datetime


class AssignmentCreateRequest(BaseModel):
    lesson_topic: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    due_at: datetime | None = None


class AssignmentResponse(BaseModel):
    assignment_id: str
    class_id: str
    class_name: str = ""
    lesson_topic: str
    description: str = ""
    due_at: datetime | None = None
    created_at: datetime


class ClassDetailResponse(ClassResponse):
    members: list[UserResponse] = []
    assignments: list[AssignmentResponse] = []


class ClassMemberAddRequest(BaseModel):
    student_email: str = Field(min_length=3, max_length=150)


class ParentChildRequest(BaseModel):
    parent_email: str = Field(min_length=3, max_length=150)
    child_email: str = Field(min_length=3, max_length=150)


# --- Knowledge Base Schemas ---

class KnowledgeDocumentResponse(BaseModel):
    doc_id: str
    teacher_email: str
    title: str
    subject: str
    grade_level: str
    file_type: str
    original_filename: str
    chunk_count: int
    created_at: datetime


class KnowledgeUploadRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    subject: str = Field(default="math", max_length=50)
    grade_level: str = Field(default="grade6", max_length=50)


class ClassKnowledgeLinkRequest(BaseModel):
    doc_id: str = Field(min_length=1, max_length=200)


# --- Student Memory Schemas ---

class StudentProfileResponse(BaseModel):
    student_email: str
    learning_style: str
    difficulty_level: str
    preferred_language: str
    strengths: str
    weaknesses: str
    notes: str
    updated_at: datetime | None = None


class StudentProfileUpdateRequest(BaseModel):
    learning_style: str | None = Field(default=None, max_length=50)
    difficulty_level: str | None = Field(default=None, max_length=50)
    strengths: str | None = Field(default=None, max_length=2000)
    weaknesses: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=2000)


class LearningMemoryResponse(BaseModel):
    memory_id: int
    student_email: str
    session_id: str
    summary: str
    topics_covered: str
    mistakes_made: str
    mastery_score: float
    created_at: datetime


class SkillAssessmentResponse(BaseModel):
    id: int
    student_email: str
    topic: str
    sub_skill: str
    correct_count: int
    total_attempts: int
    mastery_rate: float = 0.0
    last_assessed_at: datetime


# --- Voice Cloning Schemas ---

class VoiceProfileCreateRequest(BaseModel):
    voice_name: str = Field(min_length=1, max_length=100)
    provider: str = Field(default="gtts", max_length=50)


class VoiceProfileResponse(BaseModel):
    profile_id: str
    teacher_email: str
    voice_name: str
    provider: str
    model_path: str | None = None
    external_voice_id: str | None = None
    sample_count: int
    status: str
    created_at: datetime


class ClassVoiceSettingRequest(BaseModel):
    voice_profile_id: str = Field(min_length=1, max_length=200)
