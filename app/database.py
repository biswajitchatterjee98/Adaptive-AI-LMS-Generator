from __future__ import annotations

from typing import Dict, List
from uuid import UUID

from app.models import SessionState


class TemplateDatabase:
    """Base knowledge templates for domain-aware curriculum generation."""

    def __init__(self) -> None:
        self.domain_templates: Dict[str, Dict[str, List[str]]] = {
            "web development": {
                "fundamentals": ["HTML Basics", "CSS Foundations", "JavaScript Core"],
                "intermediate": ["React Components", "API Integration", "State Management"],
                "advanced": ["Performance Optimization", "System Design", "Deployment"],
            },
            "upsc": {
                "fundamentals": ["Indian Polity Basics", "History Foundations", "Geography Essentials"],
                "intermediate": ["Current Affairs Mapping", "Answer Writing", "CSAT Strategy"],
                "advanced": ["Mains Test Strategy", "Optional Deep Work", "Revision Systems"],
            },
            "spiritual studies": {
                "fundamentals": ["Core Text Overview", "Meditation Basics", "Ethics and Practice"],
                "intermediate": ["Comparative Thought", "Applied Reflection", "Practice Journaling"],
                "advanced": ["Advanced Contemplative Practice", "Teaching Framework", "Research Methods"],
            },
        }

    def get_tracks(self, domain: str) -> Dict[str, List[str]]:
        fallback = self.domain_templates["web development"]
        return self.domain_templates.get(domain.lower().strip(), fallback)


class UserSessionDatabase:
    """Dynamic store for user-specific LMS sessions and progress."""

    def __init__(self) -> None:
        self.sessions: Dict[UUID, SessionState] = {}
        self.progress_log: Dict[UUID, List[dict]] = {}

    def save_session(self, session: SessionState) -> None:
        self.sessions[session.session_id] = session

    def get_session(self, session_id: UUID) -> SessionState:
        return self.sessions[session_id]

    def append_progress(self, session_id: UUID, item: dict) -> None:
        self.progress_log.setdefault(session_id, []).append(item)

    def get_progress(self, session_id: UUID) -> List[dict]:
        return self.progress_log.get(session_id, [])
