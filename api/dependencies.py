from __future__ import annotations

from functools import lru_cache

from common.config import ConfigError, get_settings
from common.openai_client import OpenAIClient, OpenAIClientConfig
from repositories.sheets_repo import SheetsRepository, create_client
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
