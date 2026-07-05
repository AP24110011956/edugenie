from functools import lru_cache

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.schemas import (
    ExplanationRequest,
    ExplanationResponse,
    LearningPathRequest,
    LearningPathResponse,
    QARequest,
    QAResponse,
    QuizRequest,
    QuizResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.services.learning import LearningService


router = APIRouter(prefix="/api/v1", tags=["learning"])


@lru_cache
def get_learning_service() -> LearningService:
    return LearningService(get_settings())


@router.get("/health", tags=["system"])
async def health() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "status": "ok",
        "gemini_configured": bool(settings.gemini_api_key),
        "explanation_provider": settings.explanation_provider,
    }


@router.post("/qa", response_model=QAResponse)
async def answer_question(
    payload: QARequest,
    service: LearningService = Depends(get_learning_service),
) -> QAResponse:
    return await service.answer_question(payload.question)


@router.post("/explanations", response_model=ExplanationResponse)
async def explain_topic(
    payload: ExplanationRequest,
    service: LearningService = Depends(get_learning_service),
) -> ExplanationResponse:
    return await service.explain_topic(payload.topic, payload.audience_level)


@router.post("/quizzes", response_model=QuizResponse)
async def generate_quiz(
    payload: QuizRequest,
    service: LearningService = Depends(get_learning_service),
) -> QuizResponse:
    return await service.generate_quiz(payload.text, payload.question_count)


@router.post("/summaries", response_model=SummaryResponse)
async def summarize_text(
    payload: SummaryRequest,
    service: LearningService = Depends(get_learning_service),
) -> SummaryResponse:
    return await service.summarize(payload.text)


@router.post("/learning-paths", response_model=LearningPathResponse)
async def create_learning_path(
    payload: LearningPathRequest,
    service: LearningService = Depends(get_learning_service),
) -> LearningPathResponse:
    return await service.create_learning_path(payload.topic, payload.level)

