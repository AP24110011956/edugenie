from __future__ import annotations

import json
from typing import Any

import httpx

from app.services.errors import AIServiceError


class GeminiClient:
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 60.0) -> None:
        self.api_key = api_key
        self.model = model.removeprefix("models/")
        self.timeout_seconds = timeout_seconds

    async def generate_text(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        max_output_tokens: int = 2_048,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        if not self.api_key:
            raise AIServiceError(
                "Gemini is not configured. Add GEMINI_API_KEY to the .env file.",
                code="gemini_not_configured",
                status_code=503,
            )

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        }
        # Gemini 2.5 counts internal thinking against maxOutputTokens. These
        # short tutoring tasks benefit more from complete visible responses.
        if self.model.startswith("gemini-2.5-"):
            generation_config["thinkingConfig"] = {"thinkingBudget": 0}
        if response_schema:
            generation_config.update(
                {
                    "responseMimeType": "application/json",
                    "responseSchema": response_schema,
                }
            )

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        url = f"{self.base_url}/models/{self.model}:generateContent"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key,
                    },
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise AIServiceError(
                "Gemini took too long to respond. Please try again.",
                code="gemini_timeout",
                status_code=504,
            ) from exc
        except httpx.HTTPError as exc:
            raise AIServiceError(
                "Could not connect to Gemini. Please try again.",
                code="gemini_connection_error",
            ) from exc

        if response.is_error:
            self._raise_api_error(response)

        data = response.json()
        text = self._extract_text(data)
        if not text:
            raise AIServiceError(
                "Gemini returned an empty response.", code="gemini_empty_response"
            )
        return text.strip()

    async def generate_json(
        self,
        prompt: str,
        *,
        response_schema: dict[str, Any],
        temperature: float = 0.2,
        max_output_tokens: int = 4_096,
    ) -> Any:
        text = await self.generate_text(
            prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_schema=response_schema,
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIServiceError(
                "Gemini returned malformed structured data.",
                code="gemini_invalid_json",
            ) from exc

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts)

    @staticmethod
    def _raise_api_error(response: httpx.Response) -> None:
        status = response.status_code
        try:
            error = response.json().get("error", {})
            raw_message = str(error.get("message", ""))
        except (ValueError, AttributeError):
            raw_message = ""

        if status in {401, 403}:
            message = "The Gemini API key is invalid or does not have access."
            code = "gemini_auth_error"
        elif status == 429:
            message = (
                "Gemini quota or credits are unavailable. Check the project's "
                "usage and billing in Google AI Studio."
            )
            code = "gemini_quota_exceeded"
        elif status == 400:
            message = "Gemini rejected the request. Check the selected model."
            code = "gemini_bad_request"
        else:
            message = "Gemini is temporarily unavailable. Please try again."
            code = "gemini_api_error"

        if "not found" in raw_message.lower():
            message = "The configured Gemini model is unavailable."
            code = "gemini_model_unavailable"

        raise AIServiceError(message, code=code, status_code=503)
