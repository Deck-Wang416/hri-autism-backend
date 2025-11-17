"""Authentication service for user registration and login."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from common.errors import NotFoundError, ValidationError
from common.jwt_utils import create_access_token
from common.security import hash_password, verify_password
from common.time_utils import from_isoformat, to_isoformat, utc_now
from repositories.sheets_repo import SheetsRepository
from schemas.auth import AuthTokens, UserLoginRequest, UserOut, UserRegisterRequest, UserRole


class AuthService:
    def __init__(self, repository: SheetsRepository) -> None:
        self._repository = repository

    async def register(self, payload: UserRegisterRequest) -> AuthTokens:
        existing = self._repository.get_user_by_email(payload.email)
        if existing is not None:
            raise ValidationError("Email is already registered.")

        user_id = uuid4()
        now = utc_now()
        iso_now = to_isoformat(now)

        record = {
            "user_id": str(user_id),
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "full_name": payload.full_name,
            "role": payload.role.value,
            "created_at": iso_now,
            "updated_at": iso_now,
            "last_login_at": iso_now,
        }
        self._repository.create_user(record)
        user_out = self._build_user_out(record)
        token = create_access_token(
            user_id=user_out.user_id.hex,
            email=user_out.email,
            role=user_out.role.value,
        )
        return AuthTokens(access_token=token, user=user_out)

    async def login(self, payload: UserLoginRequest) -> AuthTokens:
        record = self._repository.get_user_by_email(payload.email)
        if record is None:
            raise NotFoundError("User not found.")

        if not verify_password(payload.password, record["password_hash"]):
            raise ValidationError("Invalid credentials.")

        now = utc_now()
        iso_now = to_isoformat(now)
        updated_record = self._repository.update_user(
            record["user_id"], {"last_login_at": iso_now, "updated_at": iso_now}
        )

        user_out = self._build_user_out(updated_record)
        token = create_access_token(
            user_id=user_out.user_id.hex,
            email=user_out.email,
            role=user_out.role.value,
        )
        return AuthTokens(access_token=token, user=user_out)

    def _build_user_out(self, record: dict) -> UserOut:
        return UserOut(
            user_id=UUID(record["user_id"]),
            email=record["email"],
            full_name=record["full_name"],
            role=UserRole(record["role"]),
            created_at=from_isoformat(record["created_at"]),
            updated_at=from_isoformat(record["updated_at"]),
            last_login_at=from_isoformat(record["last_login_at"])
            if record.get("last_login_at")
            else None,
        )
