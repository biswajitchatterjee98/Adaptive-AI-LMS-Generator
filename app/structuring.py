from __future__ import annotations

from app.models import LmsStrategyId, SessionState, StructuredProfile


def _infer_pace(time_commitment: str) -> str:
    value = time_commitment.lower()
    if "15" in value or "20" in value or "full" in value:
        return "fast"
    if "3" in value or "4" in value:
        return "slow"
    return "medium"


def _infer_content_type(learning_style: str) -> str:
    style = learning_style.lower()
    if "video" in style:
        return "video"
    if "text" in style:
        return "text"
    if "interactive" in style:
        return "interactive"
    return "mixed"


def _coerce_strategy(raw: str | None) -> LmsStrategyId:
    if raw in ("foundations", "balanced", "intensive"):
        return raw
    return "balanced"


def build_profile(state: SessionState) -> StructuredProfile:
    answers = state.answers
    learning_style = answers.get("learning_style", "mixed")
    time_commitment = answers.get("time_commitment", "5_hours_week")
    assessment_preference = answers.get("assessment_preference", "weekly")
    user_level = answers.get("user_level", state.target_audience)
    goal = answers.get("goal", state.goal)
    domain = answers.get("domain", state.domain)

    profile = StructuredProfile(
        domain=domain,
        user_level=user_level,
        goal=goal,
        learning_style=learning_style,
        time_commitment=time_commitment,
        assessment_preference=assessment_preference,
        content_depth=answers.get("content_depth", "balanced"),
        language=answers.get("language", "english"),
        pace=_infer_pace(time_commitment),
        content_type=_infer_content_type(learning_style),
        assessment_frequency=assessment_preference,
        lms_strategy=_coerce_strategy(answers.get("lms_strategy")),
    )
    return profile
