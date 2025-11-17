from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import jwt
from jwt import InvalidTokenError

from common.config import JWTSettings, get_settings
from common.errors import ValidationError

RoleLiteral = Literal["parent", "therapist"]


@dataclass(frozen=True)
class JWTPayload:
    sub: str
    email: str
    role: RoleLiteral
    iat: int
    exp: int
    iss: Optional[str] = None
    aud: Optional[str] = None


def _ensure_settings(settings: Optional[JWTSettings]) -> JWTSettings:
    return settings or get_settings().jwt


def create_access_token(
    *,
    user_id: str,
    email: str,
    role: RoleLiteral,
    expires_minutes: Optional[int] = None,
    settings: Optional[JWTSettings] = None,
) -> str:
    """Issue a signed JWT containing user claims."""
    jwt_settings = _ensure_settings(settings)
    lifetime = expires_minutes or jwt_settings.access_token_minutes
    now = datetime.now(timezone.utc)
    expire_at = now + timedelta(minutes=lifetime)

    payload: dict = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire_at.timestamp()),
    }
    if jwt_settings.issuer:
        payload["iss"] = jwt_settings.issuer
    if jwt_settings.audience:
        payload["aud"] = jwt_settings.audience

    return jwt.encode(payload, jwt_settings.secret_key, algorithm=jwt_settings.algorithm)


def decode_access_token(token: str, *, settings: Optional[JWTSettings] = None) -> JWTPayload:
    """Validate and decode a JWT, returning the canonical payload."""
    jwt_settings = _ensure_settings(settings)
    options = {"require": ["sub", "email", "role", "iat", "exp"]}
    try:
        decoded = jwt.decode(
            token,
            jwt_settings.secret_key,
            algorithms=[jwt_settings.algorithm],
            issuer=jwt_settings.issuer,
            audience=jwt_settings.audience,
            options=options,
        )
    except InvalidTokenError as exc:
        raise ValidationError(message="Invalid or expired authentication token.") from exc

    try:
        return JWTPayload(
            sub=str(decoded["sub"]),
            email=str(decoded["email"]),
            role=str(decoded["role"]),
            iat=int(decoded["iat"]),
            exp=int(decoded["exp"]),
            iss=decoded.get("iss"),
            aud=decoded.get("aud"),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise ValidationError(message="Malformed authentication token payload.") from exc
