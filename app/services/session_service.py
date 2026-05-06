from __future__ import annotations

from threading import Thread
from uuid import UUID, uuid4

from app.adaptive_engine import AdaptiveLearningEngine
from app.ai_interviewer import AIInterviewer
from app.generator import LMSGenerator
from app.models import (
    AdaptationResponse,
    AnswerRequest,
    GenerateLmsRequest,
    GenerationResponse,
    PlanResponse,
    ScanStatusResponse,
    PerformanceUpdateRequest,
    QuestionTurnResponse,
    SessionDetailResponse,
    SessionState,
    StartSessionRequest,
    StartSessionResponse,
)
from app.question_engine import AdaptiveQuestionEngine
from app.repository import SessionRepository
from app.planner import build_plan_preview
from app.structuring import build_profile
from app.url_context import fetch_domain_scan_summary, normalize_url, summarize_text_source


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepository,
        question_engine: AdaptiveQuestionEngine,
        lms_generator: LMSGenerator,
        adaptive_engine: AdaptiveLearningEngine,
        ai_interviewer: AIInterviewer,
    ) -> None:
        self.session_repo = session_repo
        self.question_engine = question_engine
        self.lms_generator = lms_generator
        self.adaptive_engine = adaptive_engine
        self.ai_interviewer = ai_interviewer

    def get_session(self, session_id: UUID) -> SessionState | None:
        return self.session_repo.get_session(session_id)

    def start_session(self, payload: StartSessionRequest) -> StartSessionResponse:
        normalized_url = ""
        if payload.source_type == "domain_link":
            normalized_url = normalize_url(payload.source_value)

        session = SessionState(
            session_id=uuid4(),
            source_type=payload.source_type,
            source_value=payload.source_value,
            source_summary="",
            scan_status="scanning",
            scan_progress=5,
            scan_message="Session initialized",
            domain="general learning",
            domain_url=normalized_url,
            target_audience="beginner",
            goal="knowledge",
            question_history=[],
            answers={},
            current_field=None,
            current_options=[],
        )
        self.session_repo.save_session(session)

        Thread(
            target=self._prepare_session_in_background,
            args=(session.session_id,),
            daemon=True,
        ).start()

        return StartSessionResponse(
            session_id=session.session_id,
            source_type=payload.source_type,
            first_question=None,
            first_options=[],
            source_summary="",
            scan_status="scanning",
            scan_progress=5,
            scan_message="Session initialized",
        )

    def _prepare_session_in_background(self, session_id: UUID) -> None:
        session = self.session_repo.get_session(session_id)
        if session is None:
            return

        try:
            if session.source_type == "domain_link":
                session.scan_progress = 20
                session.scan_message = "Scanning domain pages"
                self.session_repo.save_session(session)
                source_summary = fetch_domain_scan_summary(session.domain_url)
            else:
                session.scan_progress = 20
                session.scan_message = "Analyzing text brief"
                self.session_repo.save_session(session)
                source_summary = summarize_text_source(session.source_value)

            session.scan_progress = 70
            session.scan_message = "Building interview context"
            session.source_summary = source_summary
            session.answers["source_summary"] = source_summary
            self.session_repo.save_session(session)

            first_question, first_options, first_field = self.ai_interviewer.next_question_with_options(
                source_summary=source_summary,
                missing_fields=self.question_engine.missing_parameters({}),
                known_answers={},
                asked_questions=[],
            )
            session.question_history = [first_question]
            session.current_field = first_field
            session.current_options = first_options
            session.scan_status = "ready"
            session.scan_progress = 100
            session.scan_message = "Interview ready"
            self.session_repo.save_session(session)
        except Exception:
            session.scan_status = "failed"
            session.scan_progress = 100
            session.scan_message = "Failed to prepare interview"
            self.session_repo.save_session(session)

    def scan_status(self, session_id: UUID) -> ScanStatusResponse | None:
        session = self.session_repo.get_session(session_id)
        if session is None:
            return None
        first_question = session.question_history[0] if session.question_history else None
        return ScanStatusResponse(
            session_id=session_id,
            scan_status=session.scan_status,
            scan_progress=session.scan_progress,
            scan_message=session.scan_message,
            source_summary=session.source_summary,
            first_question=first_question,
            first_options=session.current_options,
        )

    def answer_session(self, session_id: UUID, payload: AnswerRequest) -> QuestionTurnResponse | None:
        session = self.session_repo.get_session(session_id)
        if session is None:
            return None
        if session.scan_status != "ready" or not session.question_history:
            return None

        current_question = session.question_history[-1]
        source_summary = session.source_summary or session.answers.get("source_summary", "")

        extracted = self.ai_interviewer.extract_updates(
            current_question=current_question,
            answer=payload.answer,
            known_answers=session.answers,
            target_field=session.current_field,
        )
        session.answers.update(extracted)
        session.answers[f"free_text_{len(session.question_history)}"] = payload.answer

        asked = len(session.question_history)
        missing = self.question_engine.missing_parameters(session.answers)
        confidence = self.question_engine.confidence_score(asked_questions=asked, missing_count=len(missing))
        session.confidence_score = confidence
        session.domain = session.answers.get("domain", session.domain)
        session.target_audience = session.answers.get("user_level", session.target_audience)
        session.goal = session.answers.get("goal", session.goal)

        stop = self.question_engine.should_stop(
            asked_questions=asked,
            confidence=confidence,
            missing_count=len(missing),
        )
        if stop:
            session.profile = build_profile(session)
            session.current_field = None
            session.current_options = []
            self.session_repo.save_session(session)
            return QuestionTurnResponse(
                session_id=session_id,
                asked_questions=asked,
                confidence_score=confidence,
                status="ready_for_generation",
                missing_parameters=missing,
            )

        next_q, next_options, next_field = self.ai_interviewer.next_question_with_options(
            source_summary=source_summary,
            missing_fields=missing,
            known_answers=session.answers,
            asked_questions=session.question_history,
        )
        session.current_field = next_field
        session.current_options = next_options
        session.question_history.append(next_q)
        self.session_repo.save_session(session)
        return QuestionTurnResponse(
            session_id=session_id,
            asked_questions=asked,
            confidence_score=confidence,
            status="questioning",
            next_question=next_q,
            next_options=next_options,
            allow_custom_answer=True,
            missing_parameters=missing,
        )

    def generate_lms(self, session_id: UUID, payload: GenerateLmsRequest | None = None) -> GenerationResponse | None:
        session = self.session_repo.get_session(session_id)
        if session is None:
            return None

        strategy_id = payload.strategy_id if payload else "balanced"
        session.answers["lms_strategy"] = strategy_id
        profile = build_profile(session)
        course = self.lms_generator.generate(profile)
        session.profile = profile
        session.course = course
        self.session_repo.save_session(session)
        return GenerationResponse(
            session_id=session_id,
            profile=profile,
            course=course,
            applied_strategy=strategy_id,
        )

    def plan_session(self, session_id: UUID) -> PlanResponse | None:
        session = self.session_repo.get_session(session_id)
        if session is None:
            return None
        return build_plan_preview(session, self.lms_generator)

    def apply_adaptation(
        self,
        session_id: UUID,
        payload: PerformanceUpdateRequest,
    ) -> AdaptationResponse | None:
        session = self.session_repo.get_session(session_id)
        if session is None:
            return None

        actions = self.adaptive_engine.adapt(payload)
        self.session_repo.add_progress_event(
            session_id=session_id,
            topic=payload.topic,
            score_percent=payload.score_percent,
            time_spent_minutes=payload.time_spent_minutes,
            engagement=payload.engagement,
            actions=actions,
        )
        self.session_repo.save_session(session)
        return AdaptationResponse(
            session_id=session_id,
            actions=actions,
            updated_recommendations=[
                "Recalculate next module unlock order",
                "Prioritize weak-topic revision queue",
                "Adjust assessment cadence per engagement",
            ],
        )

    def session_details(self, session_id: UUID) -> SessionDetailResponse | None:
        session = self.session_repo.get_session(session_id)
        if session is None:
            return None
        progress = self.session_repo.get_progress_events(session_id)
        return SessionDetailResponse(session=session, progress_events=progress)
