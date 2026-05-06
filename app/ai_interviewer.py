from __future__ import annotations

import json
import re
from typing import Dict, List, Tuple

from groq import Groq

from app.config import groq_api_key, groq_model

_STOPWORDS = frozenset(
    "a an the and or for of to in on at by from with as is are was were be been being "
    "it its this that these those your our their any all each both than then into over "
    "also just only not no yes but about after before when while can could should would "
    "will shall may might must".split()
)


class AIInterviewer:
    def __init__(self) -> None:
        key = groq_api_key()
        self.client = Groq(api_key=key) if key else None
        self.model = groq_model()

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        if self.client is None:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        t = text.strip()
        if not t.startswith("```"):
            return t
        lines = t.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @staticmethod
    def _parse_json_object(raw: str) -> dict:
        cleaned = AIInterviewer._strip_code_fence(raw)
        try:
            parsed = json.loads(cleaned)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start >= 0 and end > start:
                return json.loads(cleaned[start : end + 1])
            raise

    @staticmethod
    def _keywords_from_summary(text: str, limit: int = 10) -> List[str]:
        words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]{2,}", text or "")
        seen: set[str] = set()
        out: List[str] = []
        for w in words:
            lw = w.lower()
            if lw in _STOPWORDS or lw in seen:
                continue
            seen.add(lw)
            out.append(w[:48])
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def _unique_options_preserve_order(options: List[str]) -> List[str]:
        seen: set[str] = set()
        out: List[str] = []
        for o in options:
            s = " ".join(str(o).split()).strip()
            if not s:
                continue
            key = s.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
        return out

    def _pad_distinct_options(
        self,
        existing: List[str],
        source_summary: str,
        field: str,
    ) -> List[str]:
        """Fill up to 4 options without duplicating; tie extras to source keywords when possible."""
        out = self._unique_options_preserve_order(existing)
        if len(out) >= 4:
            return out[:4]

        seen = {x.casefold() for x in out}
        kws = self._keywords_from_summary(source_summary, 14)
        topic = kws[0] if kws else "this subject"

        templates: List[str] = [
            f"Prioritize hands-on practice related to {topic}",
            f"Balance concepts and exercises for {topic}",
            f"Orientation survey across key {topic} ideas",
            f"Deeper mastery path emphasizing {topic}",
            f"Short intensive sprint focused on {topic}",
            f"Structured progression with checkpoints on {topic}",
            f"Light overview — breadth over depth on {topic}",
            f"Scenario-based learning tied to {topic}",
        ]
        field_hints = {
            "domain": [
                f"LMS scope aligned with your source topic ({topic})",
                f"Adjacent domain that still supports {topic}",
                f"Narrow specialization within {topic}",
                f"Cross-cutting themes from your scanned content",
            ],
            "goal": [
                f"Job-ready skills from your source domain",
                f"Exam or certification outcomes",
                f"Personal enrichment around {topic}",
                f"Research or academic depth",
            ],
            "user_level": [
                "Assume learners new to the topic",
                "Mixed beginner and intermediate",
                "Mostly experienced practitioners",
                "Highly heterogeneous audience",
            ],
        }
        extras = field_hints.get(field, []) + templates

        i = 0
        while len(out) < 4 and i < len(extras) + 20:
            cand = extras[i % len(extras)]
            ck = cand.casefold()
            if ck not in seen:
                seen.add(ck)
                out.append(cand[:120])
            i += 1

        # Last resort: numbered distinct placeholders (rare)
        n = 1
        while len(out) < 4:
            cand = f"Alternative emphasis #{n} ({field})"
            if cand.casefold() not in seen:
                seen.add(cand.casefold())
                out.append(cand)
            n += 1

        return out[:4]

    def _contextual_fallback(
        self,
        field: str,
        source_summary: str,
        asked_questions: List[str],
    ) -> Tuple[str, List[str]]:
        kws = self._keywords_from_summary(source_summary, 6)
        topic = kws[0] if kws else "your scanned material"
        snippet = " ".join(source_summary.split())[:140]
        follow_up = len(asked_questions) >= 2

        if snippet and len(snippet) > 40:
            prefix = "Building on your scanned context: " if follow_up else ""
            base_q = (
                f'{prefix}"{snippet}'
                f'{"…" if len(source_summary) > 140 else ""}" — '
                f"which option fits best for '{field}'?"
            )
        else:
            base_q = (
                f'Based on your source (themes like "{topic}"), '
                f"what best describes the angle for this LMS requirement ({field})?"
            )

        options_seed = [
            f"Stay tightly aligned with {topic}",
            f"Blend {topic} with broader fundamentals",
            f"Fast-track practical outcomes for {topic}",
            f"Academic / theoretical depth on {topic}",
        ]
        opts = self._pad_distinct_options(options_seed, source_summary, field)

        if not base_q.endswith("?"):
            base_q = f"{base_q}?"
        return base_q, opts

    def extract_updates(
        self,
        current_question: str,
        answer: str,
        known_answers: Dict[str, str],
        target_field: str | None = None,
    ) -> Dict[str, str]:
        """Extract structured profile fields from a single user answer."""
        system_prompt = (
            "You extract LMS requirement fields from user answers. "
            "Return strict JSON object only. Allowed keys: "
            "domain, goal, user_level, learning_style, time_commitment, "
            "assessment_preference, content_depth, language."
        )
        user_prompt = (
            f"Current question: {current_question}\n"
            f"User answer: {answer}\n"
            f"Known values: {json.dumps(known_answers)}\n"
            f"Target field for this question: {target_field}\n"
            "Infer only values that are explicitly stated or strongly implied. "
            "If nothing inferable, return {}."
        )
        try:
            raw = self._chat(system_prompt, user_prompt)
            parsed = self._parse_json_object(raw)
            if isinstance(parsed, dict):
                return {k: str(v) for k, v in parsed.items() if isinstance(v, (str, int, float))}
            return {}
        except Exception:
            return self._fallback_extract(current_question, answer, target_field)

    def _fallback_extract(self, current_question: str, answer: str, target_field: str | None = None) -> Dict[str, str]:
        question = current_question.lower()
        value = answer.strip()
        lower_value = value.lower()

        if target_field in {
            "domain",
            "goal",
            "user_level",
            "learning_style",
            "time_commitment",
            "assessment_preference",
            "content_depth",
            "language",
        }:
            if target_field == "goal":
                for goal in ["exam", "job", "skill", "knowledge"]:
                    if goal in lower_value:
                        return {"goal": goal}
            if target_field == "user_level":
                for level in ["beginner", "intermediate", "advanced"]:
                    if level in lower_value:
                        return {"user_level": level}
            return {target_field: value}

        if "exact domain" in question or "topic" in question or "lms you want" in question:
            return {"domain": value}
        if "goal" in question:
            for goal in ["exam", "job", "skill", "knowledge"]:
                if goal in lower_value:
                    return {"goal": goal}
            return {"goal": value}
        if "current level" in question or "beginner" in question:
            for level in ["beginner", "intermediate", "advanced"]:
                if level in lower_value:
                    return {"user_level": level}
            return {"user_level": value}
        if "learning style" in question or "format" in question:
            return {"learning_style": value}
        if "hours" in question or "time" in question:
            return {"time_commitment": value}
        if "assessment" in question:
            return {"assessment_preference": value}
        if "high-level" in question or "mastery" in question or "depth" in question:
            return {"content_depth": value}
        if "language" in question:
            return {"language": value}
        return {}

    def next_question_with_options(
        self,
        source_summary: str,
        missing_fields: List[str],
        known_answers: Dict[str, str],
        asked_questions: List[str],
    ) -> Tuple[str, List[str], str | None]:
        """Generate next adaptive MCQ question with up to 4 distinct options grounded in source_summary."""
        if not missing_fields:
            opts_seed = [
                "No extra constraints",
                "Tight deadline or launch date",
                "Budget or tooling limits",
                "Need mentor or live support",
            ]
            options = self._pad_distinct_options(opts_seed, source_summary, "goal")
            return (
                "Any final constraints, preferences, or deadlines I should include before generating your LMS?",
                options,
                None,
            )

        field = missing_fields[0]
        summary_compact = " ".join(source_summary.split())[:2200]
        prior_q = asked_questions[-10:] if asked_questions else []

        system_prompt = (
            "You are an LMS requirement interviewer. Output ONLY valid JSON: "
            '{"question":"<string>","options":["<string>",...]}.\n'
            "Rules:\n"
            "1) Ask ONE concise MCQ for the given target_field.\n"
            "2) The question MUST explicitly reflect concepts, audience, or terminology from the "
            "Source summary when possible. Do not ask generic industry questions if the summary "
            "contains specific topics—name those topics or themes.\n"
            "3) Provide exactly 4 options. Each option must be DISTINCT: no duplicates, no rewording "
            "the same idea (e.g. avoid both 'Video lessons' and 'Video-based'). Max ~10 words per option.\n"
            "4) Do not repeat or paraphrase earlier questions listed under Already asked.\n"
            "5) Stay faithful to the summary; do not invent facts not supported by it."
        )
        user_prompt = (
            f"Source summary (from scanned URL or user brief):\n{summary_compact}\n\n"
            f"target_field: {field}\n"
            f"Known answers: {json.dumps(known_answers)}\n"
            f"Already asked questions (avoid similar intent): {json.dumps(prior_q)}\n"
            "Return JSON only."
        )

        try:
            raw = self._chat(system_prompt, user_prompt).strip()
            parsed = self._parse_json_object(raw)
            question = str(parsed.get("question", "")).strip()
            options = parsed.get("options", [])
            if not isinstance(options, list):
                options = []
            cleaned = self._unique_options_preserve_order([str(x).strip() for x in options if str(x).strip()])
            if len(cleaned) < 2:
                raise ValueError("Insufficient distinct options from model")
            cleaned = self._pad_distinct_options(cleaned, source_summary, field)
            if not question.endswith("?"):
                question = f"{question}?"
            return question, cleaned, field
        except Exception:
            q, opts = self._contextual_fallback(field, source_summary, asked_questions)
            return q, opts, field
