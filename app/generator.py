from __future__ import annotations

from typing import List

from app.database import TemplateDatabase
from app.models import Course, Lesson, Module, StructuredProfile, Topic


class LMSGenerator:
    def __init__(self, template_db: TemplateDatabase) -> None:
        self.template_db = template_db

    def _difficulty_track(self, user_level: str) -> str:
        if user_level == "beginner":
            return "fundamentals"
        if user_level == "advanced":
            return "advanced"
        return "intermediate"

    def _track_for_strategy(self, profile: StructuredProfile) -> str:
        """Map learner profile + chosen LMS path to a template track."""
        level = profile.user_level.lower()
        if profile.lms_strategy == "foundations":
            return "fundamentals"
        if profile.lms_strategy == "intensive":
            if level == "beginner":
                return "intermediate"
            return "advanced"
        return self._difficulty_track(profile.user_level)

    def _build_topics(self, module_title: str, level: str) -> List[Topic]:
        if level == "beginner":
            difficulty = "basic"
        elif level == "advanced":
            difficulty = "advanced"
        else:
            difficulty = "intermediate"

        return [
            Topic(title=f"{module_title} Concepts", difficulty=difficulty, estimated_minutes=45),
            Topic(title=f"{module_title} Practice", difficulty=difficulty, estimated_minutes=60),
        ]

    def generate(self, profile: StructuredProfile) -> Course:
        tracks = self.template_db.get_tracks(profile.domain)
        selected_track = self._track_for_strategy(profile)
        module_titles = tracks[selected_track]

        hours_per_module = 4
        base_weeks = 8 if profile.pace == "fast" else 12
        strategy = profile.lms_strategy
        if strategy == "foundations":
            timeline_weeks = max(10, int(round(base_weeks * 1.2)))
            hours_per_module = 5
            path_label = "Foundations path"
            revision_plan = [
                "Daily micro-reviews for new vocabulary and terms",
                "Weekly spaced revision with low-stakes checks",
                "Bi-weekly weak-area review with extra drills",
                "Final cumulative revision sprint",
            ]
        elif strategy == "intensive":
            timeline_weeks = max(6, int(round(base_weeks * 0.82)))
            hours_per_module = 3
            path_label = "Intensive track"
            revision_plan = [
                "High-frequency recall drills between modules",
                "Compressed mock cycles aligned to your goal",
                "Tight feedback loop on mistakes only",
            ]
        else:
            timeline_weeks = base_weeks
            path_label = "Balanced track"
            revision_plan = [
                "Weekly spaced revision",
                "Bi-weekly weak-area review",
                "Final cumulative revision sprint",
            ]

        modules: List[Module] = []
        for idx, title in enumerate(module_titles, start=1):
            topics = self._build_topics(title, profile.user_level)
            lesson = Lesson(
                title=f"Lesson {idx}: {title}",
                outcomes=[f"Understand and apply {title.lower()}"],
                topics=topics,
            )
            modules.append(Module(title=title, estimated_hours=hours_per_module, lessons=[lesson]))

        if profile.goal == "exam":
            assignments = ["Weekly test series", "Timed mock simulation"]
            practice_questions = ["MCQ set 1", "MCQ set 2", "Case-based practice set"]
        elif profile.goal == "skill":
            assignments = ["Build practical mini-project", "Portfolio-ready capstone"]
            practice_questions = ["Scenario challenge 1", "Scenario challenge 2"]
        else:
            assignments = ["Reflection assignment", "Concept application worksheet"]
            practice_questions = ["Comprehension quiz 1", "Comprehension quiz 2"]

        if strategy == "intensive":
            assignments = assignments + ["Sprint retrospective and velocity check"]
            practice_questions = practice_questions + ["Rapid-fire mixed practice set"]
        if strategy == "foundations":
            assignments = ["Guided scaffold worksheet"] + assignments
            practice_questions = ["Warm-up recall set"] + practice_questions

        domain_title = profile.domain.strip().title() or "Learning"
        return Course(
            title=f"{domain_title} — Adaptive LMS ({path_label})",
            timeline_weeks=timeline_weeks,
            modules=modules,
            practice_questions=practice_questions,
            assignments=assignments,
            revision_plan=revision_plan,
        )
