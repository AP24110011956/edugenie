from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "EduGenie Learning Assistant"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = 60.0
    explanation_provider: str = "gemini"
    lamini_model: str = "MBZUAI/LaMini-Flan-T5-783M"
    allowed_origins: tuple[str, ...] = (
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    )


@lru_cache
def get_settings() -> Settings:
    provider = os.getenv("EXPLANATION_PROVIDER", "gemini").strip().lower()
    if provider not in {"gemini", "lamini"}:
        provider = "gemini"

    try:
        timeout = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60"))
    except ValueError:
        timeout = 60.0

    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        gemini_timeout_seconds=max(5.0, timeout),
        explanation_provider=provider,
        lamini_model=os.getenv(
            "LAMINI_MODEL", "MBZUAI/LaMini-Flan-T5-783M"
        ).strip(),
        allowed_origins=tuple(
            origin.strip().rstrip("/")
            for origin in os.getenv(
                "ALLOWED_ORIGINS",
                "http://127.0.0.1:8000,http://localhost:8000",
            ).split(",")
            if origin.strip()
        ),
    )
