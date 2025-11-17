from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from common.config import ConfigError, get_settings
from common.errors import ValidationError
from common.jwt_utils import decode_access_token
from common.openai_client import OpenAIClient, OpenAIClientConfig
from common.time_utils import from_isoformat
from repositories.sheets_repo import SheetsRepository, create_client
from schemas.auth import UserOut, UserRole
from services.auth_service import AuthService
from services.children_service import ChildrenService
from services.sessions_service import SessionsService


@lru_cache()
def _build_openai_client() -> OpenAIClient:
    settings = get_settings()
    if not settings.openai.api_key:
        raise ConfigError("OPENAI_API_KEY must be configured to use OpenAIClient.")

    config = OpenAIClientConfig(api_key=settings.openai.api_key)
    return OpenAIClient(config)


@lru_cache()
def _build_sheets_repository() -> SheetsRepository:
    settings = get_settings()
    spreadsheet_id = settings.google_sheets.spreadsheet_id
    if not spreadsheet_id:
        raise ConfigError("GOOGLE_SHEETS_SPREADSHEET_ID is not configured.")

    client = create_client(settings.google_sheets.credentials_path)
    return SheetsRepository(client=client, spreadsheet_id=spreadsheet_id)


def get_children_service() -> ChildrenService:
    return ChildrenService(
        repository=_build_sheets_repository(),
        openai_client=_build_openai_client(),
    )


def get_sessions_service() -> SessionsService:
    return SessionsService(
        repository=_build_sheets_repository(),
        openai_client=_build_openai_client(),
    )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_auth_service() -> AuthService:
    return AuthService(repository=_build_sheets_repository())


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserOut:
    try:
        payload = decode_access_token(token)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Invalid authentication token."},
        ) from exc

    repository = _build_sheets_repository()
    user_uuid = UUID(payload.sub)
    record = repository.get_user_by_id(str(user_uuid))
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "User not found."},
        )

    return UserOut(
        user_id=user_uuid,
        email=record["email"],
        full_name=record["full_name"],
        role=UserRole(record["role"]),
        created_at=from_isoformat(record["created_at"]),
        updated_at=from_isoformat(record["updated_at"]),
        last_login_at=from_isoformat(record["last_login_at"])
        if record.get("last_login_at")
        else None,
    )
