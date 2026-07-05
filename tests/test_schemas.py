import pytest
from pydantic import ValidationError

from app.schemas import QuizQuestion


def test_quiz_answer_must_be_an_option() -> None:
    with pytest.raises(ValidationError):
        QuizQuestion(
            question="Which answer is correct?",
            options=["A", "B", "C", "D"],
            answer="E",
            explanation="Test",
        )


def test_quiz_options_must_be_unique() -> None:
    with pytest.raises(ValidationError):
        QuizQuestion(
            question="Which answer is correct?",
            options=["A", "A", "C", "D"],
            answer="A",
            explanation="Test",
        )

