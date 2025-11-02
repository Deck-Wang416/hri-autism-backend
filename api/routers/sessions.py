from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_sessions_service
from common.errors import BaseAppError, to_http_exception
from schemas.sessions import SessionCreate, SessionCreateResponse, SessionDetail
from services.sessions_service import SessionsService

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    payload: SessionCreate,
    service: SessionsService = Depends(get_sessions_service),
) -> SessionCreateResponse:
    try:
        return await service.create_session(payload)
    except BaseAppError as exc:
        raise to_http_exception(exc)


@router.get(
    "/{session_id}",
    response_model=SessionDetail,
)
async def get_session(
    session_id: str,
    service: SessionsService = Depends(get_sessions_service),
) -> SessionDetail:
    from uuid import UUID

    try:
        return await service.get_session(UUID(session_id))
    except ValueError:
        # Path param is not a valid UUID
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format.",
        )
    except BaseAppError as exc:
        raise to_http_exception(exc)
