from datetime import UTC, datetime


def utcnow() -> datetime:
    # Keep storing UTC timestamps with the existing naive-datetime semantics.
    return datetime.now(UTC).replace(tzinfo=None)
