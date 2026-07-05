from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from app.services.errors import AIServiceError


class LaMiniExplainer:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._tokenizer: Any = None
        self._model: Any = None

    async def explain(self, topic: str, audience_level: str) -> str:
        return await asyncio.to_thread(self._explain_sync, topic, audience_level)

    def _explain_sync(self, topic: str, audience_level: str) -> str:
        self._ensure_loaded()
        prompt = (
            f"Explain {topic} clearly for a {audience_level} learner. "
            "Use simple language, one helpful example, and a short takeaway."
        )
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=280,
            do_sample=False,
            num_beams=3,
        )
        return self._tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise AIServiceError(
                "Local explanations require requirements-lamini.txt to be installed.",
                code="lamini_dependencies_missing",
                status_code=503,
            ) from exc

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self._model.eval()
        except Exception as exc:
            raise AIServiceError(
                "The local explanation model could not be loaded.",
                code="lamini_load_error",
                status_code=503,
            ) from exc


@lru_cache
def get_lamini_explainer(model_name: str) -> LaMiniExplainer:
    return LaMiniExplainer(model_name)

