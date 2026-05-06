from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.config import database_url
from app.persistence_models import Base


ENGINE = create_engine(database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=ENGINE)
    inspector = inspect(ENGINE)
    if "sessions" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("sessions")}
        with ENGINE.begin() as conn:
            if "domain_url" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN domain_url VARCHAR(1024) NOT NULL DEFAULT ''"))
            if "source_type" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN source_type VARCHAR(32) NOT NULL DEFAULT 'text'"))
            if "source_value" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN source_value VARCHAR(4096) NOT NULL DEFAULT ''"))
            if "source_summary" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN source_summary VARCHAR(4000) NOT NULL DEFAULT ''"))
            if "scan_status" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN scan_status VARCHAR(16) NOT NULL DEFAULT 'scanning'"))
            if "scan_progress" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN scan_progress INTEGER NOT NULL DEFAULT 0"))
            if "scan_message" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN scan_message VARCHAR(255) NOT NULL DEFAULT 'Initializing'"))
            if "current_field" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN current_field VARCHAR(64) NULL"))
            if "current_options" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN current_options JSON NOT NULL DEFAULT '[]'"))
