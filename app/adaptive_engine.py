from __future__ import annotations

from typing import List

from app.models import PerformanceUpdateRequest


class AdaptiveLearningEngine:
    def adapt(self, performance: PerformanceUpdateRequest) -> List[str]:
        actions: List[str] = []

        if performance.score_percent < 50:
            actions.append(f"Add reinforcement module for '{performance.topic}'.")
            actions.append("Recommend revision before unlocking advanced lessons.")
        elif performance.score_percent > 85:
            actions.append(f"Skip repeated basics in '{performance.topic}'.")
            actions.append("Increase difficulty for upcoming topics.")
        else:
            actions.append("Keep current sequence with targeted practice.")

        if performance.time_spent_minutes > 120 and performance.engagement == "low":
            actions.append("Shorten next lesson chunks for attention retention.")
        elif performance.engagement == "high":
            actions.append("Introduce optional stretch tasks.")

        return actions
