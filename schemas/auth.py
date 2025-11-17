from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    parent = "parent"
    therapist = "therapist"


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


class AuthTokens(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
