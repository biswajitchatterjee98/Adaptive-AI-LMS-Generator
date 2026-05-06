from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Course, SessionState, StructuredProfile
from app.persistence_models import ProgressEventORM, SessionORM


class SessionRepository:
    def save_session(self, state: SessionState) -> None:
        with SessionLocal() as db:
            row = db.get(SessionORM, str(state.session_id))
            payload_profile = state.profile.model_dump() if state.profile else None
            payload_course = state.course.model_dump() if state.course else None

            if row is None:
                row = SessionORM(
                    session_id=str(state.session_id),
                    source_type=state.source_type,
                    source_value=state.source_value,
                    source_summary=state.source_summary,
                    scan_status=state.scan_status,
                    scan_progress=state.scan_progress,
                    scan_message=state.scan_message,
                    domain=state.domain,
                    domain_url=state.domain_url,
                    target_audience=state.target_audience,
                    goal=state.goal,
                    question_history=state.question_history,
                    answers=state.answers,
                    current_field=state.current_field,
                    current_options=state.current_options,
                    confidence_score=state.confidence_score,
                    profile=payload_profile,
                    course=payload_course,
                )
                db.add(row)
            else:
                row.source_type = state.source_type
                row.source_value = state.source_value
                row.source_summary = state.source_summary
                row.scan_status = state.scan_status
                row.scan_progress = state.scan_progress
                row.scan_message = state.scan_message
                row.domain = state.domain
                row.domain_url = state.domain_url
                row.target_audience = state.target_audience
                row.goal = state.goal
                row.question_history = state.question_history
                row.answers = state.answers
                row.current_field = state.current_field
                row.current_options = state.current_options
                row.confidence_score = state.confidence_score
                row.profile = payload_profile
                row.course = payload_course
            db.commit()

    def get_session(self, session_id: UUID) -> Optional[SessionState]:
        with SessionLocal() as db:
            row = db.get(SessionORM, str(session_id))
            if row is None:
                return None
            return SessionState(
                session_id=UUID(row.session_id),
                source_type=row.source_type,
                source_value=row.source_value,
                source_summary=row.source_summary,
                scan_status=row.scan_status,
                scan_progress=row.scan_progress,
                scan_message=row.scan_message,
                domain=row.domain,
                domain_url=row.domain_url,
                target_audience=row.target_audience,
                goal=row.goal,
                question_history=row.question_history or [],
                answers=row.answers or {},
                current_field=row.current_field,
                current_options=row.current_options or [],
                confidence_score=row.confidence_score or 0.0,
                profile=StructuredProfile.model_validate(row.profile) if row.profile else None,
                course=Course.model_validate(row.course) if row.course else None,
            )

    def add_progress_event(
        self,
        session_id: UUID,
        topic: str,
        score_percent: float,
        time_spent_minutes: int,
        engagement: str,
        actions: List[str],
    ) -> None:
        with SessionLocal() as db:
            row = ProgressEventORM(
                session_id=str(session_id),
                topic=topic,
                score_percent=score_percent,
                time_spent_minutes=time_spent_minutes,
                engagement=engagement,
                actions=actions,
            )
            db.add(row)
            db.commit()

    def get_progress_events(self, session_id: UUID) -> List[dict]:
        with SessionLocal() as db:
            rows = db.execute(
                select(ProgressEventORM).where(ProgressEventORM.session_id == str(session_id)).order_by(ProgressEventORM.id.asc())
            ).scalars()
            return [
                {
                    "id": row.id,
                    "topic": row.topic,
                    "score_percent": row.score_percent,
                    "time_spent_minutes": row.time_spent_minutes,
                    "engagement": row.engagement,
                    "actions": row.actions,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
