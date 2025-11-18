from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class GoogleSheetsSettings:
    credentials_path: Path
    spreadsheet_id: Optional[str]


@dataclass(frozen=True)
class OpenAISettings:
    api_key: Optional[str]


@dataclass(frozen=True)
class JWTSettings:
    secret_key: str
    algorithm: str
    issuer: Optional[str]
    audience: Optional[str]
    access_token_minutes: int


@dataclass(frozen=True)
class Settings:
    environment: str
    google_sheets: GoogleSheetsSettings
    openai: OpenAISettings
    jwt: JWTSettings


def _read_required_path(env_name: str) -> Path:
    raw = os.getenv(env_name)
    if not raw:
        raise ConfigError(f"Missing required environment variable: {env_name}")

    path = Path(raw).expanduser()
    if not path.exists():
        raise ConfigError(f"Path defined by {env_name} does not exist: {path}")

    return path


def _read_optional(env_name: str) -> Optional[str]:
    value = os.getenv(env_name)
    return value.strip() if value and value.strip() else None


def _read_required(env_name: str) -> str:
    value = _read_optional(env_name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {env_name}")
    return value


def _read_int(env_name: str, default: int) -> int:
    raw = _read_optional(env_name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{env_name} must be an integer.") from exc


def _resolve_google_credentials_path() -> Path:
    """
    Render deployments provide the service account JSON via an env var.
    Write it to a temp file so gspread can load it; otherwise fall back
    to the legacy GOOGLE_SHEETS_CREDENTIALS_PATH.
    """
    credentials_json = _read_optional("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if credentials_json:
        tmp_dir = Path(tempfile.gettempdir())
        tmp_path = tmp_dir / "google_sheets_credentials.json"
        tmp_path.write_text(credentials_json)
        return tmp_path

    return _read_required_path("GOOGLE_SHEETS_CREDENTIALS_PATH")


@lru_cache()
def get_settings() -> Settings:
    """Load application settings from environment variables."""
    credentials_path = _resolve_google_credentials_path()

    return Settings(
        environment=_read_optional("APP_ENV") or "development",
        google_sheets=GoogleSheetsSettings(
            credentials_path=credentials_path,
            spreadsheet_id=_read_optional("GOOGLE_SHEETS_SPREADSHEET_ID"),
        ),
        openai=OpenAISettings(api_key=_read_optional("OPENAI_API_KEY")),
        jwt=JWTSettings(
            secret_key=_read_required("JWT_SECRET_KEY"),
            algorithm=_read_optional("JWT_ALGORITHM") or "HS256",
            issuer=_read_optional("JWT_ISSUER"),
            audience=_read_optional("JWT_AUDIENCE"),
            access_token_minutes=_read_int("JWT_ACCESS_TOKEN_MINUTES", 60),
        ),
    )
