from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_children_service
from common.errors import BaseAppError, to_http_exception
from schemas.children import ChildCreate, ChildCreateResponse, ChildDetail
from services.children_service import ChildrenService

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
    "/{child_id}",
    response_model=ChildDetail,
)
async def get_child_profile(
    child_id: str,
    service: ChildrenService = Depends(get_children_service),
) -> ChildDetail:
    from uuid import UUID

    try:
        return await service.get_child(UUID(child_id))
    except ValueError:
        # Path param is not a valid UUID
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid child_id format.",
            )
    except BaseAppError as exc:
        raise to_http_exception(exc)
