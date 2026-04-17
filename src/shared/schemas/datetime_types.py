from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer


def ensure_utc_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def serialize_utc_datetime(value: datetime) -> str:
    return ensure_utc_aware(value).isoformat()


UTCDateTime = Annotated[
    datetime,
    AfterValidator(ensure_utc_aware),
    PlainSerializer(serialize_utc_datetime, return_type=str, when_used="json"),
]
