"""Business logic for managing session records and prompt generation."""

from __future__ import annotations

import asyncio
from typing import Iterable, List
from uuid import UUID, uuid4

from common.openai_client import OpenAIClient
from common.errors import NotFoundError
from common.time_utils import from_isoformat, to_isoformat, utc_now
from repositories.sheets_repo import SheetsRepository
from schemas.children import ChildDetail, CommunicationLevel, PersonalityType
from schemas.sessions import (
    LatestSessionResponse,
    SessionCreate,
    SessionCreateResponse,
    SessionDetail,
    SessionMood,
)


class SessionsService:
    """Coordinates prompt generation and persistence for session records."""

    SESSION_SYSTEM_PROMPT = (
        "You are drafting a system-level instruction for a social companion robot that supports autistic children."
        "The output must describe the robot's role, tone, behavioral guidelines, and concrete interaction strategies based on the provided Child profile and Today's context."
        "Do not speak directly to the child. Produce a single cohesive system prompt for the robot to follow."
    )

    def __init__(self, repository: SheetsRepository, openai_client: OpenAIClient) -> None:
        self._repository = repository
        self._openai = openai_client

    async def create_session(self, payload: SessionCreate) -> SessionCreateResponse:
        """Create a new session, generate prompt, and persist the record."""
        child_record = await asyncio.to_thread(
            self._repository.get_child, str(payload.child_id)
        )
        child_profile = self._hydrate_child(child_record)

        prompt_messages = self._build_prompt_messages(child_profile, payload)
        prompt_text = await self._openai.generate_prompt(
            system_instructions=self.SESSION_SYSTEM_PROMPT,
            template_messages=prompt_messages,
        )

        session_uuid = uuid4()
        now = utc_now()
        iso_now = to_isoformat(now)

        record = {
            "session_id": str(session_uuid),
            "child_id": str(child_profile.child_id),
            "mood": payload.mood.value,
            "environment": payload.environment,
            "situation": payload.situation,
            "prompt": prompt_text,
            "created_at": iso_now,
        }

        await asyncio.to_thread(self._repository.create_session, record)

        return SessionCreateResponse(
            session_id=session_uuid,
            prompt=prompt_text,
            created_at=now,
        )

    async def get_session(self, session_id: UUID) -> SessionDetail:
        """Retrieve a stored session record."""
        record = await asyncio.to_thread(self._repository.get_session, str(session_id))

        return SessionDetail(
            session_id=UUID(record["session_id"]),
            child_id=UUID(record["child_id"]),
            mood=SessionMood(record["mood"]),
            environment=record["environment"],
            situation=record["situation"],
            prompt=record["prompt"],
            created_at=from_isoformat(record["created_at"]),
        )
    
    # Convert the sheet dict to ChildDetail
    def _hydrate_child(self, record: dict) -> ChildDetail:
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
            created_at=from_isoformat(record["created_at"]),
            updated_at=from_isoformat(record["updated_at"]),
        )
    
    # Child's profile + The day's session
    def _build_prompt_messages(
        self, child: ChildDetail, payload: SessionCreate
    ) -> Iterable[dict]:
        profile_lines = [
            f"Nickname: {child.nickname}",
            f"Age: {child.age}",
            f"Communication level: {child.comm_level.value}",
            f"Personality: {child.personality.value}",
            f"Long-term interests: {child.interests}",
            f"Sensitivities to avoid: {child.triggers}",
            f"Target social skills: {child.target_skills}",
        ]

        session_lines = [
            f"Mood today: {payload.mood.value}",
            f"Environment tags: {payload.environment}",
            f"Situation notes: {payload.situation}",
        ]

        profile_text = "Child profile:\n" + "\n".join(f"- {line}" for line in profile_lines)
        session_text = "Today's context:\n" + "\n".join(f"- {line}" for line in session_lines)

        messages: List[dict] = [
            {"role": "user", "content": profile_text},
            {"role": "user", "content": session_text},
        ]
        return messages

    async def get_latest_session(self, user_id: UUID, child_id: UUID) -> LatestSessionResponse | None:
        owns = await asyncio.to_thread(
            self._repository.user_owns_child, str(user_id), str(child_id)
        )
        if not owns:
            raise NotFoundError("Child not found for current user.")

        record = await asyncio.to_thread(
            self._repository.get_latest_session_for_child, str(child_id)
        )
        if record is None:
            return None

        return LatestSessionResponse(
            session_id=UUID(record["session_id"]),
            child_id=UUID(record["child_id"]),
            mood=SessionMood(record["mood"]),
            environment=record["environment"],
            situation=record["situation"],
            prompt=record["prompt"],
            created_at=from_isoformat(record["created_at"]),
        )
