# SOP Implementation Mapping

This file maps each section of the provided SOP to implemented code.

## 1) Objective

Implemented via API workflow in `app/main.py`:
- Collect user input
- Ask adaptive questions
- Structure requirements
- Generate LMS roadmap
- Adapt based on performance updates

## 2) Core Workflow

1. User enters domain URL (`/api/session/start`)
2. AI interview with adaptive questions (`/api/session/{id}/answer`)
3. Schema structuring (`app/structuring.py`)
4. LMS generation (`/api/session/{id}/generate-lms`)
5. Adaptation loop (`/api/session/{id}/performance`)

## 3) Key Components

- Input Layer: request models in `app/models.py`
- AI Question Engine: `app/question_engine.py`, `app/ai_interviewer.py`
- URL Context Extraction: `app/url_context.py`
- Data Structuring Layer: `app/structuring.py`
- LMS Generation Engine: `app/generator.py`
- Adaptive Learning Engine: `app/adaptive_engine.py`
- Database Layer:
  - Base templates: `app/database.py`
  - PostgreSQL session engine and ORM: `app/db.py`, `app/persistence_models.py`, `app/repository.py`

## 4) Decision Logic

Implemented in generation and adaptation logic:
- Beginner -> fundamentals track
- Advanced -> advanced track
- Exam goal -> test-focused assignments
- Skill goal -> project-focused assignments

## 5) User Journey SOP

Complete journey is exposed through API endpoints and frontend dashboard:
- Dashboard UI: `/` from `frontend/index.html`
- API-driven flow: Entry -> Interview -> Generation -> Learning -> Adaptation

## 6) Metrics and Quality Control

Starter instrumentation points:
- `confidence_score` in question engine
- progress events persisted in `progress_events` table
- adaptation actions logged per performance event

## 7) Error Handling and Risks

- Missing session -> HTTP 404
- Insufficient data handled by continued questioning until required fields are captured
- Confidence threshold and min/max question constraints enforced

## 8) Security Notes

Current version uses PostgreSQL persistence and API-level data modeling.
Recommended next production hardening:
- Add authenticated persistence
- Encrypt stored PII
- Anonymize behavior analytics
- Keep personal data isolated from model prompts
