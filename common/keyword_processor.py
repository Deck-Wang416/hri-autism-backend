from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable, List

from common.errors import ValidationError

KEYWORD_DELIMITER = ","
KEYWORD_MIN = 1
KEYWORD_MAX = 7


@dataclass(frozen=True)
class KeywordRequest:
    """Input payload for keyword extraction."""

    label: str # "triggers", "interests", "target_skills"
    raw_text: str


def _normalize_tokens(tokens: Iterable[str]) -> List[str]:
    normalized: List[str] = []
    for token in tokens:
        cleaned = token.strip().lower().replace(" ", "_")
        if not cleaned:
            continue
        if cleaned in normalized:
            continue
        normalized.append(cleaned)
    return normalized


def _validate_token_count(tokens: List[str], *, label: str) -> None:
    if not (KEYWORD_MIN <= len(tokens) <= KEYWORD_MAX):
        raise ValidationError(
            message=(
                f"{label} must contain between {KEYWORD_MIN} and {KEYWORD_MAX} keywords, "
                f"got {len(tokens)}."
            ),
            details={"label": label, "count": len(tokens)},
        )


def format_keywords(tokens: Iterable[str]) -> str:
    """Normalize iterable of tokens into canonical comma-separated string."""
    normalized = _normalize_tokens(tokens)
    _validate_token_count(normalized, label="keywords")
    return KEYWORD_DELIMITER.join(normalized)


# async prompt -> keyword string returned by LLM client
KeywordGenerator = Callable[[str], Awaitable[str]]


class KeywordProcessor:
    """High level helper for generating and formatting keyword strings."""

    def __init__(self, generator: KeywordGenerator) -> None:
        self._generate = generator

    async def process(self, request: KeywordRequest) -> str:
        """Generate processed keywords from raw text."""
        raw = request.raw_text.strip()
        if not raw:
            raise ValidationError(
                message=f"{request.label}_raw cannot be empty.", details={"label": request.label}
            )

        prompt = self._build_prompt(request)
        response = await self._generate(prompt)
        tokens = self._parse_response(response, label=request.label)
        return format_keywords(tokens)

    def _build_prompt(self, request: KeywordRequest) -> str:
        """Craft the instruction prompt for the LLM."""
        instructions = (
            "You are an assistant that extracts concise, lowercase keywords from parental notes.\n"
            "Return between 1 and 7 keywords separated by commas. Replace spaces with underscores.\n"
            f"Label: {request.label}\n"
            "The value after “Label:” only tells you the keyword category, do not include the label itself or any prefix in the output.\n"
            "Input text:\n"
            f"{request.raw_text.strip()}"
        )
        return instructions

    def _parse_response(self, response: str, *, label: str) -> List[str]:
        """Convert the LLM response string into a list of tokens."""
        if not response:
            raise ValidationError(
                message=f"Keyword generation returned empty response for {label}.",
                details={"label": label},
            )

        raw_tokens = response.split(KEYWORD_DELIMITER)
        return [token for token in raw_tokens if token.strip()]
