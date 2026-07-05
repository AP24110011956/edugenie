from __future__ import annotations

from app.core.config import Settings
from app.schemas import (
    ExplanationResponse,
    LearningPathResponse,
    QAResponse,
    QuizQuestion,
    QuizResponse,
    SummaryResponse,
)
from app.services.errors import AIServiceError
from app.services.explanation import get_lamini_explainer
from app.services.gemini import GeminiClient


QA_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "answer": {"type": "STRING"},
        "reasoning": {"type": "STRING"},
    },
    "required": ["answer", "reasoning"],
}

QUIZ_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "question": {"type": "STRING"},
            "options": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "minItems": 4,
                "maxItems": 4,
            },
            "answer": {"type": "STRING"},
            "explanation": {"type": "STRING"},
        },
        "required": ["question", "options", "answer", "explanation"],
    },
}

LEARNING_PATH_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "overview": {"type": "STRING"},
        "stages": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "objective": {"type": "STRING"},
                    "topics": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "activities": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                    },
                },
                "required": ["title", "objective", "topics", "activities"],
            },
        },
        "resources": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {
                        "type": "STRING",
                        "enum": [
                            "course",
                            "video",
                            "article",
                            "book",
                            "practice",
                            "other",
                        ],
                    },
                    "suggestion": {"type": "STRING"},
                },
                "required": ["type", "suggestion"],
            },
        },
    },
    "required": ["overview", "stages", "resources"],
}


class LearningService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.gemini = GeminiClient(
            settings.gemini_api_key,
            settings.gemini_model,
            settings.gemini_timeout_seconds,
        )

    async def answer_question(self, question: str) -> QAResponse:
        prompt = f"""
You are EduGenie, a careful educational tutor. Return two separate fields:
1. "answer": a direct, self-contained answer. Lead with the conclusion and
   keep it concise. Do not include internal deliberation or a long preamble.
2. "reasoning": a brief, learner-friendly explanation of the key facts or
   verification steps supporting the answer. This is a concise rationale, not
   private chain-of-thought. State uncertainty instead of inventing facts.

Student question: {question}
""".strip()
        data = await self.gemini.generate_json(
            prompt,
            response_schema=QA_SCHEMA,
            max_output_tokens=2_048,
        )
        try:
            return QAResponse.model_validate(
                {**data, "model": self.settings.gemini_model}
            )
        except (TypeError, ValueError) as exc:
            raise AIServiceError(
                "Gemini returned an invalid answer structure.",
                code="invalid_answer_structure",
            ) from exc

    async def explain_topic(
        self, topic: str, audience_level: str
    ) -> ExplanationResponse:
        if self.settings.explanation_provider == "lamini":
            explainer = get_lamini_explainer(self.settings.lamini_model)
            explanation = await explainer.explain(topic, audience_level)
            return ExplanationResponse(
                explanation=explanation,
                provider="lamini",
                model=self.settings.lamini_model,
            )

        prompt = f"""
Explain the topic below to a {audience_level} learner. Use plain language,
build the idea step by step, include one concrete example or analogy, and end
with a one-sentence takeaway.

Topic: {topic}
""".strip()
        explanation = await self.gemini.generate_text(
            prompt, max_output_tokens=1_500
        )
        return ExplanationResponse(
            explanation=explanation,
            provider="gemini",
            model=self.settings.gemini_model,
        )

    async def generate_quiz(self, text: str, count: int) -> QuizResponse:
        prompt = f"""
Create exactly {count} multiple-choice questions using only the supplied
passage. Each question must have exactly four distinct options. The answer
must exactly equal one option. Add a short explanation of why it is correct.
Avoid trick questions.

Passage:
{text}
""".strip()
        data = await self.gemini.generate_json(
            prompt,
            response_schema=QUIZ_SCHEMA,
            max_output_tokens=8_192,
        )
        try:
            questions = [QuizQuestion.model_validate(item) for item in data]
        except (TypeError, ValueError) as exc:
            raise AIServiceError(
                "Gemini returned an invalid quiz structure.",
                code="invalid_quiz_structure",
            ) from exc
        if len(questions) != count:
            raise AIServiceError(
                "Gemini returned the wrong number of quiz questions.",
                code="invalid_quiz_count",
            )
        return QuizResponse(questions=questions, model=self.settings.gemini_model)

    async def summarize(self, text: str) -> SummaryResponse:
        prompt = f"""
Summarize the educational text below for revision. Preserve its central facts
and relationships, remove repetition, and return a concise readable summary.
Do not introduce information absent from the source.

Text:
{text}
""".strip()
        summary = await self.gemini.generate_text(prompt, max_output_tokens=1_500)
        return SummaryResponse(summary=summary, model=self.settings.gemini_model)

    async def create_learning_path(
        self, topic: str, level: str
    ) -> LearningPathResponse:
        if level == "all":
            level_instruction = (
                "Cover the complete progression through beginner, intermediate, "
                "and advanced levels. Clearly label every stage with its level."
            )
        else:
            level_instruction = (
                f"Begin at the {level} level and keep the plan appropriate for "
                f"a {level} learner."
            )
        prompt = f"""
Design a practical, ordered learning path for the topic "{topic}".
{level_instruction}
Include learning objectives, concepts, and hands-on activities. For one level,
provide 4 to 6 stages. For all levels, provide 6 to 9 stages spanning the full
progression. Suggest resource categories or reputable search targets; do not
invent URLs or claim unavailable course details.
""".strip()
        data = await self.gemini.generate_json(
            prompt,
            response_schema=LEARNING_PATH_SCHEMA,
            max_output_tokens=4_096,
        )
        try:
            return LearningPathResponse.model_validate(
                {
                    **data,
                    "topic": topic,
                    "level": level,
                    "model": self.settings.gemini_model,
                }
            )
        except (TypeError, ValueError) as exc:
            raise AIServiceError(
                "Gemini returned an invalid learning path structure.",
                code="invalid_learning_path",
            ) from exc
