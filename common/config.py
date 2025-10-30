from __future__ import annotations

import os
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
class Settings:
    environment: str
    google_sheets: GoogleSheetsSettings
    openai: OpenAISettings


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


@lru_cache()
def get_settings() -> Settings:
    """Load application settings from environment variables."""
    credentials_path = _read_required_path("GOOGLE_SHEETS_CREDENTIALS_PATH")

    return Settings(
        environment=_read_optional("APP_ENV") or "development",
        google_sheets=GoogleSheetsSettings(
            credentials_path=credentials_path,
            spreadsheet_id=_read_optional("GOOGLE_SHEETS_SPREADSHEET_ID"),
        ),
        openai=OpenAISettings(api_key=_read_optional("OPENAI_API_KEY")),
    )
