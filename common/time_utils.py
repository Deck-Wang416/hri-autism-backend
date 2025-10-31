from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def to_isoformat(dt: datetime, *, keep_microseconds: bool = False) -> str:
    """Serialize a datetime to ISO-8601 string in UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    if not keep_microseconds:
        dt = dt.replace(microsecond=0)

    iso = dt.isoformat()
    return iso.replace("+00:00", "Z")


def from_isoformat(value: str) -> datetime:
    """Parse an ISO-8601 string into a datetime."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt
