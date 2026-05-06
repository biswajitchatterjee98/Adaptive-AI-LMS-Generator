from __future__ import annotations

from typing import Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


LmsStrategyId = Literal["foundations", "balanced", "intensive"]


class StartSessionRequest(BaseModel):
    source_type: Literal["text", "domain_link"]
    source_value: str = Field(..., min_length=2)


class StartSessionResponse(BaseModel):
    session_id: UUID
    source_type: Literal["text", "domain_link"]
    first_question: Optional[str] = None
    first_options: List[str] = Field(default_factory=list)
    source_summary: str = ""
    scan_status: Literal["scanning", "ready", "failed"] = "scanning"
    scan_progress: int = 0
    scan_message: str = "Initializing"
    min_questions: int = 5
    max_questions: int = 10


class ScanStatusResponse(BaseModel):
    session_id: UUID
    scan_status: Literal["scanning", "ready", "failed"]
    scan_progress: int
    scan_message: str
    source_summary: str = ""
    first_question: Optional[str] = None
    first_options: List[str] = Field(default_factory=list)


class AnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1)


class QuestionTurnResponse(BaseModel):
    session_id: UUID
    asked_questions: int
    confidence_score: float
    status: Literal["questioning", "ready_for_generation"]
    next_question: Optional[str] = None
    next_options: List[str] = Field(default_factory=list)
    allow_custom_answer: bool = True
    missing_parameters: List[str] = Field(default_factory=list)


class StructuredProfile(BaseModel):
    domain: str
    user_level: str
    goal: str
    learning_style: str = "mixed"
    time_commitment: str = "5_hours_week"
    assessment_preference: str = "weekly"
    content_depth: str = "balanced"
    language: str = "english"
    pace: str = "medium"
    content_type: str = "interactive"
    assessment_frequency: str = "weekly"
    lms_strategy: LmsStrategyId = "balanced"


class Topic(BaseModel):
    title: str
    difficulty: Literal["basic", "intermediate", "advanced"]
    estimated_minutes: int


class Lesson(BaseModel):
    title: str
    outcomes: List[str]
    topics: List[Topic]


class Module(BaseModel):
    title: str
    estimated_hours: int
    lessons: List[Lesson]


class Course(BaseModel):
    title: str
    timeline_weeks: int
    modules: List[Module]
    practice_questions: List[str]
    assignments: List[str]
    revision_plan: List[str]


class GenerationResponse(BaseModel):
    session_id: UUID
    profile: StructuredProfile
    course: Course
    applied_strategy: LmsStrategyId = "balanced"


class LmsStrategyOption(BaseModel):
    id: LmsStrategyId
    title: str
    subtitle: str
    timeline_weeks: int
    highlights: List[str] = Field(default_factory=list)
    roadmap_preview: List[Dict[str, str]] = Field(default_factory=list)


class PlanResponse(BaseModel):
    session_id: UUID
    source_summary: str
    profile_preview: Dict[str, str]
    roadmap_preview: List[Dict[str, str]]
    recommendations: List[str]
    readiness_score: float
    confidence_low: bool = False
    confidence_threshold: float = 0.85
    lms_strategy_options: List[LmsStrategyOption] = Field(default_factory=list)
    recommended_strategy_id: LmsStrategyId = "balanced"


class GenerateLmsRequest(BaseModel):
    strategy_id: LmsStrategyId = "balanced"


class PerformanceUpdateRequest(BaseModel):
    topic: str
    score_percent: float = Field(..., ge=0, le=100)
    time_spent_minutes: int = Field(..., gt=0)
    engagement: Literal["low", "medium", "high"]


class AdaptationResponse(BaseModel):
    session_id: UUID
    actions: List[str]
    updated_recommendations: List[str]


class SessionState(BaseModel):
    session_id: UUID
    source_type: Literal["text", "domain_link"] = "text"
    source_value: str = ""
    source_summary: str = ""
    scan_status: Literal["scanning", "ready", "failed"] = "scanning"
    scan_progress: int = 0
    scan_message: str = "Initializing"
    domain: str
    domain_url: str
    target_audience: str
    goal: str
    question_history: List[str] = Field(default_factory=list)
    answers: Dict[str, str] = Field(default_factory=dict)
    current_field: Optional[str] = None
    current_options: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    profile: Optional[StructuredProfile] = None
    course: Optional[Course] = None


class SessionDetailResponse(BaseModel):
    session: SessionState
    progress_events: List[dict] = Field(default_factory=list)
