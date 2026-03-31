from __future__ import annotations

import asyncio

from openai import AsyncOpenAI

from src.config.settings import get_settings


class OpenAIGenerationService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: AsyncOpenAI | None = None

    async def generate(self, prompt: str, grounding_snippets: list[str]) -> tuple[str, bool]:
        if not prompt.strip():
            raise ValueError('Prompt must be non-empty')

        composed_prompt = prompt
        if grounding_snippets:
            composed_prompt = (
                f"Use the following grounded context when relevant:\n{chr(10).join(grounding_snippets)}\n\n"
                f"User prompt: {prompt}"
            )

        try:
            # Placeholder SDK call path; tests can monkeypatch for live integration.
            await asyncio.sleep(0)
            return f"Governed response: {composed_prompt[:400]}", False
        except Exception:
            return self._generate_with_rest_fallback(composed_prompt), True

    def _generate_with_rest_fallback(self, composed_prompt: str) -> str:
        # Deterministic fallback for controlled-failure tests and offline demo mode.
        return f"Fallback governed response: {composed_prompt[:400]}"
