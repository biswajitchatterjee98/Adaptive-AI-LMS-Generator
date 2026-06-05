from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def mongodb_url() -> str:
    return os.getenv("MONGODB_URL", "mongodb://localhost:27017/adaptive_ai_lms")


def groq_api_key() -> str | None:
    return os.getenv("GROQ_API_KEY")


def groq_model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [item.strip() for item in raw.split(",") if item.strip()]
