from datetime import datetime, timezone

from sqlalchemy import event
from sqlalchemy.orm import Session as SASession

from src.shared.models.base_model import MyBaseModel


@event.listens_for(SASession, "before_flush")
def set_deleted_at_on_soft_delete(session, flush_context, instances) -> None:
    # Soft delete: when an entity is marked inactive, set deleted_at automatically.
    for obj in session.dirty:
        if isinstance(obj, MyBaseModel):
            if obj.is_active is False and obj.deleted_at is None:
                obj.deleted_at = datetime.now(timezone.utc)

    # Convert physical deletes into soft deletes (DELETE -> UPDATE).
    for obj in list(session.deleted):
        if isinstance(obj, MyBaseModel):
            obj.is_active = False
            if obj.deleted_at is None:
                obj.deleted_at = datetime.now(timezone.utc)

            # Re-add the object so SQLAlchemy cancels the DELETE and issues an UPDATE instead.
            session.add(obj)
