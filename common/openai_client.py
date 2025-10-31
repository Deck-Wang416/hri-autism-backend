from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Sequence

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from common.errors import ExternalServiceError, ValidationError
from common.keyword_processor import KeywordRequest, KeywordProcessor

DEFAULT_KEYWORD_MODEL = "gpt-4o-mini"
DEFAULT_PROMPT_MODEL = "gpt-4o"


@dataclass(frozen=True)
class OpenAIClientConfig:
    api_key: str
    keyword_model: str = DEFAULT_KEYWORD_MODEL
    prompt_model: str = DEFAULT_PROMPT_MODEL


class OpenAIClient:
    """Wrapper around the OpenAI async client with high-level helpers."""

    def __init__(self, config: OpenAIClientConfig) -> None:
        if not config.api_key:
            raise ValidationError("OPENAI_API_KEY is missing or empty.")

        self._config = config
        self._client = AsyncOpenAI(api_key=config.api_key)
        self._keyword_processor = KeywordProcessor(self._generate_keyword_completion)

    async def generate_keywords(self, requests: Sequence[KeywordRequest]) -> Dict[str, str]:
        """Generate normalized keyword strings for multiple raw text requests."""
        results: Dict[str, str] = {}
        for request in requests:
            processed = await self._keyword_processor.process(request)
            results[request.label] = processed
        return results

    async def generate_prompt(
        self,
        *,
        system_instructions: str,
        template_messages: Iterable[ChatCompletionMessageParam],
    ) -> str:
        """Generate a session prompt using chat completions."""
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_instructions}
        ]
        messages.extend(template_messages)

        try:
            completion = await self._client.chat.completions.create(
                model=self._config.prompt_model,
                messages=messages,
                temperature=0.3,
                max_tokens=800,
            )
        except Exception as exc:
            raise ExternalServiceError("Failed to generate session prompt.") from exc

        return self._extract_message_text(completion.choices[0].message.content)

    async def _generate_keyword_completion(self, prompt: str) -> str:
        """Internal helper for keyword generation requests."""
        try:
            completion = await self._client.responses.create(
                model=self._config.keyword_model,
                input=prompt,
                temperature=0.2,
                max_output_tokens=120,
            )
        except Exception as exc:
            raise ExternalServiceError("Failed to generate keywords.") from exc

        if not completion.output:
            raise ExternalServiceError("OpenAI keyword response had no output.")

        # Extract all text segments from the response
        text_parts = [
            block.text.value
            for block in completion.output
            if getattr(block, "type", "") == "output_text" and getattr(block, "text", None)
        ]

        if not text_parts:
            raise ExternalServiceError("OpenAI keyword response contained no text blocks.")

        return "".join(text_parts).strip()

    @staticmethod
    def _extract_message_text(content: Optional[Any]) -> str:
        if content is None:
            raise ExternalServiceError("OpenAI prompt response was empty.")

        if isinstance(content, str):
            text = content.strip()
            if not text:
                raise ExternalServiceError("OpenAI prompt response text was blank.")
            return text

        if isinstance(content, list):
            parts = [segment.get("text", "").strip() for segment in content if isinstance(segment, dict)]
            text = " ".join(part for part in parts if part)
            if not text:
                raise ExternalServiceError("OpenAI prompt response segments were empty.")
            return text

        raise ExternalServiceError("Unexpected OpenAI response format.")
