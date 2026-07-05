from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class QARequest(StrictModel):
    question: str = Field(min_length=3, max_length=2_000)


class QAResponse(StrictModel):
    answer: str
    reasoning: str
    model: str


class ExplanationRequest(StrictModel):
    topic: str = Field(min_length=2, max_length=500)
    audience_level: Literal["beginner", "intermediate", "advanced"] = "beginner"


class ExplanationResponse(StrictModel):
    explanation: str
    provider: Literal["gemini", "lamini"]
    model: str


class QuizRequest(StrictModel):
    text: str = Field(min_length=20, max_length=20_000)
    question_count: int = Field(default=3, ge=1, le=10)


class QuizQuestion(StrictModel):
    question: str = Field(min_length=3)
    options: list[str] = Field(min_length=4, max_length=4)
    answer: str
    explanation: str = ""

    @model_validator(mode="after")
    def answer_must_match_an_option(self) -> "QuizQuestion":
        if len(set(self.options)) != 4:
            raise ValueError("Quiz options must be unique")
        if self.answer not in self.options:
            raise ValueError("Quiz answer must exactly match one option")
        return self


class QuizResponse(StrictModel):
    questions: list[QuizQuestion]
    model: str


class SummaryRequest(StrictModel):
    text: str = Field(min_length=30, max_length=30_000)


class SummaryResponse(StrictModel):
    summary: str
    model: str


class LearningPathRequest(StrictModel):
    topic: str = Field(min_length=2, max_length=500)
    level: Literal["beginner", "intermediate", "advanced", "all"] = "beginner"


class LearningStage(StrictModel):
    title: str
    objective: str
    topics: list[str] = Field(min_length=1)
    activities: list[str] = Field(default_factory=list)


class LearningResource(StrictModel):
    type: Literal["course", "video", "article", "book", "practice", "other"]
    suggestion: str


class LearningPathResponse(StrictModel):
    topic: str
    level: str
    overview: str
    stages: list[LearningStage] = Field(min_length=1)
    resources: list[LearningResource] = Field(default_factory=list)
    model: str
