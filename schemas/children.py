from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

KEYWORD_MIN = 1
KEYWORD_MAX = 7


def _normalize_keywords(value: str) -> str:
    tokens: List[str] = [token.strip() for token in value.split(",") if token.strip()]
    if not (KEYWORD_MIN <= len(tokens) <= KEYWORD_MAX):
        raise ValueError(
            f"Each keyword field must contain between {KEYWORD_MIN} and {KEYWORD_MAX} items."
        )
    for token in tokens:
        if " " in token:
            raise ValueError("Keywords must not contain spaces.")
        if token != token.lower():
            raise ValueError("Keywords must be lowercase.")
    return ",".join(tokens)


class CommunicationLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class PersonalityType(str, Enum):
    shy = "shy"
    active = "active"
    calm = "calm"
    curious = "curious"


class ChildCreate(BaseModel):
    """POST /api/children request payload."""

    nickname: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=0, le=120)
    comm_level: CommunicationLevel
    personality: PersonalityType
    triggers_raw: str = Field(..., min_length=1, max_length=4000)
    interests_raw: str = Field(..., min_length=1, max_length=4000)
    target_skills_raw: str = Field(..., min_length=1, max_length=4000)


class ChildCreateResponse(BaseModel):
    """POST /api/children response payload."""

    child_id: UUID
    nickname: str
    age: int = Field(..., ge=0, le=120)
    triggers: str
    interests: str
    target_skills: str
    created_at: datetime
    updated_at: datetime

    @field_validator("triggers", "interests", "target_skills")
    @classmethod
    def validate_keywords(cls, value: str) -> str:
        return _normalize_keywords(value)


class ChildDetail(BaseModel):
    """GET /api/children/{child_id} response payload."""

    child_id: UUID
    nickname: str
    age: int = Field(..., ge=0, le=120)
    comm_level: CommunicationLevel
    personality: PersonalityType
    triggers_raw: str = Field(..., min_length=1, max_length=4000)
    triggers: str
    interests_raw: str = Field(..., min_length=1, max_length=4000)
    interests: str
    target_skills_raw: str = Field(..., min_length=1, max_length=4000)
    target_skills: str
    created_at: datetime
    updated_at: datetime

    @field_validator("triggers", "interests", "target_skills")
    @classmethod
    def validate_keywords(cls, value: str) -> str:
        return _normalize_keywords(value)
