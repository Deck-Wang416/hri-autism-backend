from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_children_service, get_current_user, get_sessions_service
from common.errors import BaseAppError, to_http_exception
from schemas.auth import UserOut
from schemas.children import (
    ChildCreate,
    ChildCreateResponse,
    ChildDetail,
    ChildrenListResponse,
)
from schemas.sessions import LatestSessionResponse
from services.children_service import ChildrenService
from services.sessions_service import SessionsService

router = APIRouter(prefix="/api/children", tags=["children"])


@router.post(
    "",
    response_model=ChildCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_child_profile(
    payload: ChildCreate,
    service: ChildrenService = Depends(get_children_service),
) -> ChildCreateResponse:
    try:
        return await service.create_child(payload)
    except BaseAppError as exc:
        raise to_http_exception(exc)


@router.get(
    "",
    response_model=ChildrenListResponse,
)
async def list_children(
    current_user: UserOut = Depends(get_current_user),
    service: ChildrenService = Depends(get_children_service),
) -> ChildrenListResponse:
    return await service.list_children_for_user(current_user.user_id)


@router.get(
    "/{child_id}",
    response_model=ChildDetail,
)
async def get_child_profile(
    child_id: UUID,
    service: ChildrenService = Depends(get_children_service),
) -> ChildDetail:
    try:
        return await service.get_child(child_id)
    except BaseAppError as exc:
        raise to_http_exception(exc)


@router.get(
    "/{child_id}/sessions/latest",
    response_model=LatestSessionResponse | None,
)
async def get_latest_session(
    child_id: UUID,
    current_user: UserOut = Depends(get_current_user),
    service: SessionsService = Depends(get_sessions_service),
) -> LatestSessionResponse | None:
    try:
        return await service.get_latest_session(current_user.user_id, child_id)
    except BaseAppError as exc:
        raise to_http_exception(exc)
