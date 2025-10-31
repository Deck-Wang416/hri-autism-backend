from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


@dataclass(frozen=True)
class AppErrorMeta:
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class BaseAppError(Exception):
    """Base error for all domain-specific failures."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code: str = "internal_error"
    default_message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message or self.default_message)
        self.meta = AppErrorMeta(
            code=code or self.default_code,
            message=message or self.default_message,
            details=details,
        )


class ValidationError(BaseAppError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "validation_error"
    default_message = "Request validation failed."


class NotFoundError(BaseAppError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"
    default_message = "Requested resource does not exist."


class ConflictError(BaseAppError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"
    default_message = "Resource conflict encountered."


class UnauthorizedError(BaseAppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "unauthorized"
    default_message = "Authentication required."


class ForbiddenError(BaseAppError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "forbidden"
    default_message = "You do not have access to this resource."


class ExternalServiceError(BaseAppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "external_service_error"
    default_message = "External dependency is unavailable."


class InternalServerError(BaseAppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = "internal_error"
    default_message = "An unexpected error occurred."


def to_http_exception(error: BaseAppError) -> HTTPException:
    """Convert an application error into a FastAPI HTTPException."""
    payload = {"code": error.meta.code, "message": error.meta.message}
    if error.meta.details:
        payload["details"] = error.meta.details

    return HTTPException(status_code=error.status_code, detail=payload)
