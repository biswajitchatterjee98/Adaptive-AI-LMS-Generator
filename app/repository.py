from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from app.db import progress_events_collection, sessions_collection
from app.models import Course, SessionState, StructuredProfile


class SessionRepository:
    def save_session(self, state: SessionState) -> None:
        sessions_collection().update_one(
            {"session_id": str(state.session_id)},
            {
                "$set": {
                    "source_type": state.source_type,
                    "source_value": state.source_value,
                    "source_summary": state.source_summary,
                    "scan_status": state.scan_status,
                    "scan_progress": state.scan_progress,
                    "scan_message": state.scan_message,
                    "domain": state.domain,
                    "domain_url": state.domain_url,
                    "target_audience": state.target_audience,
                    "goal": state.goal,
                    "question_history": state.question_history,
                    "answers": state.answers,
                    "current_field": state.current_field,
                    "current_options": state.current_options,
                    "confidence_score": state.confidence_score,
                    "profile": state.profile.model_dump() if state.profile else None,
                    "course": state.course.model_dump() if state.course else None,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {
                    "session_id": str(state.session_id),
                    "created_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )

    def get_session(self, session_id: UUID) -> Optional[SessionState]:
        row = sessions_collection().find_one({"session_id": str(session_id)})
        if row is None:
            return None
        return SessionState(
            session_id=UUID(row["session_id"]),
            source_type=row.get("source_type", "text"),
            source_value=row.get("source_value", ""),
            source_summary=row.get("source_summary", ""),
            scan_status=row.get("scan_status", "scanning"),
            scan_progress=row.get("scan_progress", 0),
            scan_message=row.get("scan_message", "Initializing"),
            domain=row.get("domain", ""),
            domain_url=row.get("domain_url", ""),
            target_audience=row.get("target_audience", ""),
            goal=row.get("goal", ""),
            question_history=row.get("question_history") or [],
            answers=row.get("answers") or {},
            current_field=row.get("current_field"),
            current_options=row.get("current_options") or [],
            confidence_score=row.get("confidence_score") or 0.0,
            profile=StructuredProfile.model_validate(row["profile"]) if row.get("profile") else None,
            course=Course.model_validate(row["course"]) if row.get("course") else None,
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
        events = progress_events_collection()
        last = events.find_one({"session_id": str(session_id)}, sort=[("id", -1)])
        next_id = 1 if last is None else int(last.get("id", 0)) + 1
        events.insert_one(
            {
                "id": next_id,
                "session_id": str(session_id),
                "topic": topic,
                "score_percent": score_percent,
                "time_spent_minutes": time_spent_minutes,
                "engagement": engagement,
                "actions": actions,
                "created_at": datetime.now(timezone.utc),
            }
        )

    def get_progress_events(self, session_id: UUID) -> List[dict]:
        rows = progress_events_collection().find({"session_id": str(session_id)}).sort("id", 1)
        return [
            {
                "id": int(row.get("id", 0)),
                "topic": row.get("topic", ""),
                "score_percent": float(row.get("score_percent", 0.0)),
                "time_spent_minutes": int(row.get("time_spent_minutes", 0)),
                "engagement": row.get("engagement", "medium"),
                "actions": row.get("actions") or [],
                "created_at": row.get("created_at", datetime.now(timezone.utc)).isoformat(),
            }
            for row in rows
        ]
