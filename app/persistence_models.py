from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class SessionORM(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="text")
    source_value: Mapped[str] = mapped_column(String(4096), nullable=False, default="")
    source_summary: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    scan_status: Mapped[str] = mapped_column(String(16), nullable=False, default="scanning")
    scan_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scan_message: Mapped[str] = mapped_column(String(255), nullable=False, default="Initializing")
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    domain_url: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    target_audience: Mapped[str] = mapped_column(String(32), nullable=False)
    goal: Mapped[str] = mapped_column(String(32), nullable=False)
    question_history: Mapped[list] = mapped_column(JSON, nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, nullable=False)
    current_field: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_options: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    course: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ProgressEventORM(Base):
    __tablename__ = "progress_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    score_percent: Mapped[float] = mapped_column(Float, nullable=False)
    time_spent_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement: Mapped[str] = mapped_column(String(16), nullable=False)
    actions: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
