# Adaptive AI LMS Generator Platform

This project builds a personalized LMS from either a user-provided website link or a text brief.

## What this includes

- Source intake layer (`text` or `domain_link`)
- Domain scan engine for same-site context extraction
- AI interview engine powered by Groq for adaptive questioning (grounded in scanned/brief context)
- Click-to-answer MCQ flow (tap an option to submit instantly; “Other” supports custom input)
- Data structuring layer that converts user responses into a normalized schema
- LMS generation engine (Course -> Modules -> Lessons -> Topics)
- Adaptive learning engine that updates the learning path based on performance
- MongoDB-backed persistence for sessions and progress events
- Separate backend API and frontend client

## Quick start (with MongoDB)

1. Start MongoDB:

```bash
docker compose up -d
```

2. Create and activate virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
export MONGODB_URL="mongodb://localhost:27017/adaptive_ai_lms"
export GROQ_API_KEY="your_groq_api_key_here"
export GROQ_MODEL="llama-3.3-70b-versatile"
```

4. Start backend API:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5. Start frontend (separate terminal):

```bash
cd frontend
npm install
npm run dev
```

6. Open:

- Frontend: http://127.0.0.1:5173
- Backend API docs: http://127.0.0.1:8000/docs
- Backend health: http://127.0.0.1:8000/health

## API flow

1. `POST /api/session/start` with:
   - `source_type`: `text` or `domain_link`
   - `source_value`: text brief or URL
2. Poll `GET /api/session/{session_id}/scan-status` until `scan_status` becomes `ready`
3. Repeat `POST /api/session/{session_id}/answer` until `status` becomes `ready_for_generation`
3. `GET /api/session/{session_id}/plan` to preview full plan
4. `POST /api/session/{session_id}/generate-lms`
5. `POST /api/session/{session_id}/performance` to adapt roadmap over time
6. `GET /api/session/{session_id}` to view persisted session and progress

## Notes

- If `GROQ_API_KEY` is unavailable or model calls fail, fallback deterministic questions are used.
- The interview layer enforces distinct MCQ options and tries to keep questions tied to the scanned/brief context.
- You can replace `TemplateDatabase` content with domain-specific knowledge packs.
- Frontend (React + Vite) uses `VITE_API_BASE_URL`, falling back to localStorage `API_BASE_URL`, then `http://127.0.0.1:8000`.
