from __future__ import annotations

from app.generator import LMSGenerator
from app.models import LmsStrategyId, LmsStrategyOption, PlanResponse, SessionState
from app.structuring import build_profile

_CONFIDENCE_THRESHOLD = 0.85


def _roadmap_rows(course) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for module in course.modules:
        rows.append(
            {
                "module": module.title,
                "hours": str(module.estimated_hours),
                "focus": module.lessons[0].outcomes[0] if module.lessons else "Core learning objective",
            }
        )
    return rows


def _strategy_meta(strategy_id: LmsStrategyId) -> tuple[str, str, list[str]]:
    if strategy_id == "foundations":
        return (
            "Steady foundations",
            "Extra scaffolding, slower pacing, and stronger revision loops.",
            ["Best when confidence is lower or the audience is mixed-level", "Prioritizes clarity over speed"],
        )
    if strategy_id == "intensive":
        return (
            "Intensive track",
            "Tighter timeline, more drills, and accelerated milestones.",
            ["Strong when time is limited or stakes are high", "Expect a heavier weekly load"],
        )
    return (
        "Balanced program",
        "Default blend of depth, practice, and sustainable pacing.",
        ["Works for most teams and solo learners", "Calibrated to your stated level and goal"],
    )


def _recommended_strategy(profile, confidence_low: bool) -> LmsStrategyId:
    if confidence_low:
        return "foundations"
    if profile.goal == "exam":
        return "intensive"
    if profile.goal == "skill":
        return "balanced"
    return "balanced"


def build_plan_preview(session: SessionState, lms_generator: LMSGenerator) -> PlanResponse:
    profile = build_profile(session)
    readiness = min(1.0, max(0.0, session.confidence_score))
    confidence_low = readiness < _CONFIDENCE_THRESHOLD
    recommended = _recommended_strategy(profile, confidence_low)

    options: list[LmsStrategyOption] = []
    for strategy_id in ("foundations", "balanced", "intensive"):
        variant = profile.model_copy(update={"lms_strategy": strategy_id})
        course = lms_generator.generate(variant)
        title, subtitle, highlights = _strategy_meta(strategy_id)
        options.append(
            LmsStrategyOption(
                id=strategy_id,
                title=title,
                subtitle=subtitle,
                timeline_weeks=course.timeline_weeks,
                highlights=highlights,
                roadmap_preview=_roadmap_rows(course)[:4],
            )
        )

    default_course = lms_generator.generate(profile.model_copy(update={"lms_strategy": recommended}))
    roadmap_preview = _roadmap_rows(default_course)

    recommendations = [
        "Confirm timeline and weekly commitment before generation.",
        "Review module order to match business priorities.",
        "Include custom assessments for critical outcomes.",
    ]
    if profile.goal == "exam":
        recommendations.append("Prioritize test series and revision cycles.")
    if profile.goal == "skill":
        recommendations.append("Add project milestones and portfolio checkpoints.")
    if confidence_low:
        recommendations.append(
            "Interview confidence is below threshold — compare the three LMS paths and pick the safest fit.",
        )

    return PlanResponse(
        session_id=session.session_id,
        source_summary=session.source_summary or session.answers.get("source_summary", ""),
        profile_preview={
            "domain": profile.domain,
            "goal": profile.goal,
            "user_level": profile.user_level,
            "learning_style": profile.learning_style,
            "time_commitment": profile.time_commitment,
            "language": profile.language,
        },
        roadmap_preview=roadmap_preview,
        recommendations=recommendations,
        readiness_score=round(readiness, 2),
        confidence_low=confidence_low,
        confidence_threshold=_CONFIDENCE_THRESHOLD,
        lms_strategy_options=options,
        recommended_strategy_id=recommended,
    )
