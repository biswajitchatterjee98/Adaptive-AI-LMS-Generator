from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.adaptive_engine import AdaptiveLearningEngine
from app.ai_interviewer import AIInterviewer
from app.config import cors_origins
from app.database import TemplateDatabase
from app.db import init_db
from app.generator import LMSGenerator
from starlette.requests import Request

from app.models import (
    AdaptationResponse,
    AnswerRequest,
    GenerateLmsRequest,
    GenerationResponse,
    PlanResponse,
    PerformanceUpdateRequest,
    QuestionTurnResponse,
    ScanStatusResponse,
    SessionDetailResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from app.question_engine import AdaptiveQuestionEngine
from app.repository import SessionRepository
from app.services.session_service import SessionService

app = FastAPI(title="Adaptive AI LMS Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

template_db = TemplateDatabase()
session_repo = SessionRepository()
question_engine = AdaptiveQuestionEngine()
lms_generator = LMSGenerator(template_db)
adaptive_engine = AdaptiveLearningEngine()
ai_interviewer = AIInterviewer()
session_service = SessionService(
    session_repo=session_repo,
    question_engine=question_engine,
    lms_generator=lms_generator,
    adaptive_engine=adaptive_engine,
    ai_interviewer=ai_interviewer,
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    return {
        "service": "Adaptive AI LMS Backend",
        "status": "ok",
        "docs": "/docs",
    }


@app.post("/api/session/start", response_model=StartSessionResponse)
def start_session(payload: StartSessionRequest) -> StartSessionResponse:
    try:
        return session_service.start_session(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/session/{session_id}/answer", response_model=QuestionTurnResponse)
def answer_question(session_id: UUID, payload: AnswerRequest) -> QuestionTurnResponse:
    response = session_service.answer_session(session_id, payload)
    if response is None:
        status = session_service.scan_status(session_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=409, detail="Interview is not ready yet")
    return response


@app.post("/api/session/{session_id}/generate-lms", response_model=GenerationResponse)
async def generate_lms(session_id: UUID, request: Request) -> GenerationResponse:
    try:
        raw = await request.json()
    except Exception:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    payload = GenerateLmsRequest.model_validate(raw)
    response = session_service.generate_lms(session_id, payload)
    if response is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return response


@app.get("/api/session/{session_id}/plan", response_model=PlanResponse)
def plan_session(session_id: UUID) -> PlanResponse:
    response = session_service.plan_session(session_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return response


@app.post("/api/session/{session_id}/performance", response_model=AdaptationResponse)
def apply_adaptation(session_id: UUID, payload: PerformanceUpdateRequest) -> AdaptationResponse:
    response = session_service.apply_adaptation(session_id, payload)
    if response is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return response


@app.get("/api/session/{session_id}", response_model=SessionDetailResponse)
def session_details(session_id: UUID) -> SessionDetailResponse:
    response = session_service.session_details(session_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return response


@app.get("/api/session/{session_id}/scan-status", response_model=ScanStatusResponse)
def session_scan_status(session_id: UUID) -> ScanStatusResponse:
    response = session_service.scan_status(session_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return response
