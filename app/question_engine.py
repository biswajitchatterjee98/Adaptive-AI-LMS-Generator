from __future__ import annotations

from typing import Dict, List


REQUIRED_PARAMETERS = [
    "domain",
    "goal",
    "user_level",
    "learning_style",
    "time_commitment",
    "assessment_preference",
    "content_depth",
    "language",
]


class AdaptiveQuestionEngine:
    def __init__(self, min_questions: int = 5, max_questions: int = 10, threshold: float = 0.85) -> None:
        self.min_questions = min_questions
        self.max_questions = max_questions
        self.threshold = threshold

        self.base_questions: Dict[str, str] = {
            "domain": "Based on your website, what exact domain/topic should this LMS focus on?",
            "goal": "What is your primary goal: exam, job, skill, or knowledge?",
            "user_level": "What is your current level: beginner, intermediate, or advanced?",
            "learning_style": "What is your preferred learning format: video, text, interactive, or mixed?",
            "time_commitment": "How much time can you commit each week?",
            "assessment_preference": "How often do you want assessments?",
            "content_depth": "Do you want high-level coverage or deep mastery?",
            "language": "Which language should the LMS use?",
        }

    def first_question(self, source_summary: str) -> str:
        return (
            "I reviewed your link. In one line, tell me exactly what LMS you want from it. "
            f"Context I detected: {source_summary}"
        )

    def missing_parameters(self, answers: Dict[str, str]) -> List[str]:
        return [param for param in REQUIRED_PARAMETERS if param not in answers]

    def confidence_score(self, asked_questions: int, missing_count: int) -> float:
        completion = max(0.0, 1.0 - (missing_count / len(REQUIRED_PARAMETERS)))
        depth_bonus = min(1.0, asked_questions / self.max_questions) * 0.2
        return round(min(1.0, completion * 0.8 + depth_bonus), 2)

    def next_question(self, answers: Dict[str, str], asked_questions: int) -> str:
        missing = self.missing_parameters(answers)
        if missing:
            return self.base_questions[missing[0]]

        if asked_questions < self.max_questions:
            return "Any constraints or special preferences to personalize your roadmap further?"
        return "No further questions required."

    def should_stop(self, asked_questions: int, confidence: float, missing_count: int) -> bool:
        if asked_questions >= self.max_questions:
            return True
        if asked_questions < self.min_questions:
            return False
        return confidence >= self.threshold and missing_count == 0
