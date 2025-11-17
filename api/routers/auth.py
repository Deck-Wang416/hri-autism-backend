"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from api.dependencies import get_auth_service, get_current_user
from common.errors import BaseAppError, to_http_exception
from schemas.auth import AuthTokens, UserLoginRequest, UserOut, UserRegisterRequest
from services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthTokens,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthTokens:
    try:
        return await service.register(payload)
    except BaseAppError as exc:
        raise to_http_exception(exc)


@router.post(
    "/login",
    response_model=AuthTokens,
)
async def login(
    payload: UserLoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthTokens:
    try:
        return await service.login(payload)
    except BaseAppError as exc:
        raise to_http_exception(exc)


@router.get(
    "/me",
    response_model=UserOut,
)
async def get_me(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    return current_user
