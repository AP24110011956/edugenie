from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_learning_service
from app.main import app
from app.schemas import (
    ExplanationResponse,
    LearningPathResponse,
    QAResponse,
    QuizQuestion,
    QuizResponse,
    SummaryResponse,
)


class FakeLearningService:
    async def answer_question(self, question: str) -> QAResponse:
        return QAResponse(
            answer=f"A clear answer to: {question}",
            reasoning="A concise explanation of the supporting facts.",
            model="test-model",
        )

    async def explain_topic(
        self, topic: str, audience_level: str
    ) -> ExplanationResponse:
        return ExplanationResponse(
            explanation=f"A {audience_level} explanation of {topic}.",
            provider="gemini",
            model="test-model",
        )

    async def generate_quiz(self, text: str, count: int) -> QuizResponse:
        questions = [
            QuizQuestion(
                question=f"Question {number}?",
                options=["Alpha", "Beta", "Gamma", "Delta"],
                answer="Alpha",
                explanation="The passage supports Alpha.",
            )
            for number in range(1, count + 1)
        ]
        return QuizResponse(questions=questions, model="test-model")

    async def summarize(self, text: str) -> SummaryResponse:
        return SummaryResponse(summary="A concise test summary.", model="test-model")

    async def create_learning_path(
        self, topic: str, level: str
    ) -> LearningPathResponse:
        return LearningPathResponse.model_validate(
            {
                "topic": topic,
                "level": level,
                "overview": "A practical learning plan.",
                "stages": [
                    {
                        "title": "Foundations",
                        "objective": "Learn the basics.",
                        "topics": ["Core concepts"],
                        "activities": ["Complete one exercise"],
                    }
                ],
                "resources": [
                    {"type": "practice", "suggestion": "Build a small project"}
                ],
                "model": "test-model",
            }
        )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_learning_service] = lambda: FakeLearningService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
