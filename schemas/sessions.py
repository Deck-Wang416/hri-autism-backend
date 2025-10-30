"""Pydantic models for sessions API payloads."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SessionMood(str, Enum):
    calm = "calm"
    happy = "happy"
    anxious = "anxious"
    uncomfortable = "uncomfortable"
    angry = "angry"
    tired = "tired"


LOCATION_VALUES = {"loc_indoor", "loc_outdoor"}
NOISE_VALUES = {"noise_quiet", "noise_moderate", "noise_noisy"}
CROWD_VALUES = {"crowd_alone", "crowd_few", "crowd_many"}


def _normalize_environment(value: str) -> str:
    tokens: List[str] = [token.strip() for token in value.split(",") if token.strip()]
    if len(tokens) != 3:
        raise ValueError("Environment must contain exactly three tokens.")

    location, noise, crowd = tokens
    if location not in LOCATION_VALUES:
        raise ValueError(f"Invalid location token: {location}")
    if noise not in NOISE_VALUES:
        raise ValueError(f"Invalid noise token: {noise}")
    if crowd not in CROWD_VALUES:
        raise ValueError(f"Invalid crowd token: {crowd}")

    for token in tokens:
        if " " in token:
            raise ValueError("Environment tokens must not contain spaces.")

    return ",".join(tokens)


class SessionCreate(BaseModel):
    """POST /api/sessions request payload."""

    child_id: UUID
    mood: SessionMood
    environment: str
    situation: str = Field(..., min_length=1, max_length=800)

    @validator("environment")
    def validate_environment(cls, value: str) -> str:
        return _normalize_environment(value)


class SessionCreateResponse(BaseModel):
    """POST /api/sessions response payload."""

    session_id: UUID
    prompt: str
    created_at: datetime


class SessionDetail(BaseModel):
    """GET /api/sessions/{session_id} response payload."""

    session_id: UUID
    child_id: UUID
    mood: SessionMood
    environment: str
    situation: str = Field(..., min_length=1, max_length=800)
    prompt: str
    created_at: datetime

    @validator("environment")
    def validate_environment(cls, value: str) -> str:
        return _normalize_environment(value)
