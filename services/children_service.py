from __future__ import annotations

import asyncio
from typing import Dict, List, Sequence
from uuid import UUID, uuid4

from common.keyword_processor import KeywordRequest
from common.openai_client import OpenAIClient
from common.time_utils import from_isoformat, to_isoformat, utc_now
from repositories.sheets_repo import SheetsRepository
from schemas.children import (
    ChildCreate,
    ChildCreateResponse,
    ChildDetail,
    ChildSummary,
    ChildrenListResponse,
    CommunicationLevel,
    PersonalityType,
)


class ChildrenService:
    """Coordinates keyword generation and Sheets persistence for child profiles."""

    def __init__(self, repository: SheetsRepository, openai_client: OpenAIClient) -> None:
        self._repository = repository
        self._openai = openai_client

    async def create_child(self, payload: ChildCreate, user_id: UUID) -> ChildCreateResponse:
        """Create a new child profile and persist it to Google Sheets."""
        child_uuid = uuid4()
        now = utc_now()
        iso_now = to_isoformat(now)

        keyword_requests: Sequence[KeywordRequest] = (
            KeywordRequest(label="triggers", raw_text=payload.triggers_raw),
            KeywordRequest(label="interests", raw_text=payload.interests_raw),
            KeywordRequest(label="target_skills", raw_text=payload.target_skills_raw),
        )
        keywords = await self._openai.generate_keywords(keyword_requests)

        record: Dict[str, str] = {
            "child_id": str(child_uuid),
            "nickname": payload.nickname,
            "age": str(payload.age),
            "comm_level": payload.comm_level.value,
            "personality": payload.personality.value,
            "triggers_raw": payload.triggers_raw,
            "triggers": keywords["triggers"],
            "interests_raw": payload.interests_raw,
            "interests": keywords["interests"],
            "target_skills_raw": payload.target_skills_raw,
            "target_skills": keywords["target_skills"],
            "created_at": iso_now,
            "updated_at": iso_now,
        }

        # offload synchronous Sheets write to a thread to avoid blocking
        await asyncio.to_thread(self._repository.create_child, record)
        await asyncio.to_thread(
            self._repository.link_user_child,
            {
                "user_id": str(user_id),
                "child_id": str(child_uuid),
                "created_at": iso_now,
            },
        )

        return ChildCreateResponse(
            child_id=child_uuid,
            nickname=payload.nickname,
            age=payload.age,
            triggers=keywords["triggers"],
            interests=keywords["interests"],
            target_skills=keywords["target_skills"],
            created_at=now,
            updated_at=now,
        )

    async def get_child(self, child_id: UUID, user_id: UUID | None = None) -> ChildDetail:
        """Retrieve a stored child profile."""
        if user_id is not None:
            owns = await asyncio.to_thread(
                self._repository.user_owns_child, str(user_id), str(child_id)
            )
            if not owns:
                raise NotFoundError("Child not found for current user.")

        record = await asyncio.to_thread(self._repository.get_child, str(child_id))

        # Convert ISO-8601 string into datetime
        created_at = from_isoformat(record["created_at"])
        updated_at = from_isoformat(record["updated_at"])

        return ChildDetail(
            child_id=UUID(record["child_id"]),
            nickname=record["nickname"],
            age=int(record["age"]) if isinstance(record["age"], str) else record["age"],
            comm_level=CommunicationLevel(record["comm_level"]),
            personality=PersonalityType(record["personality"]),
            triggers_raw=record["triggers_raw"],
            triggers=record["triggers"],
            interests_raw=record["interests_raw"],
            interests=record["interests"],
            target_skills_raw=record["target_skills_raw"],
            target_skills=record["target_skills"],
            created_at=created_at,
            updated_at=updated_at,
        )

    async def list_children_for_user(self, user_id: UUID) -> ChildrenListResponse:
        records: List[Dict[str, Any]] = await asyncio.to_thread(
            self._repository.list_children_for_user, str(user_id)
        )
        summaries: List[ChildSummary] = []
        for record in records:
            summaries.append(
                ChildSummary(
                    child_id=UUID(record["child_id"]),
                    nickname=record["nickname"],
                    age=int(record["age"]) if isinstance(record["age"], str) else record["age"],
                    comm_level=CommunicationLevel(record["comm_level"]),
                    personality=PersonalityType(record["personality"]),
                    triggers=record["triggers"],
                    interests=record["interests"],
                    target_skills=record["target_skills"],
                    created_at=from_isoformat(record["created_at"]),
                    updated_at=from_isoformat(record["updated_at"]),
                )
            )
        return ChildrenListResponse(children=summaries)
