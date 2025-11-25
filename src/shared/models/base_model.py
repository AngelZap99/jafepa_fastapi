from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, DateTime, func


class MyBaseModel(SQLModel):
    # Id primary key, auto increment, nullable=False, public
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: datetime = Field(
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),  # Set value on INSERT
        },
    )

    updated_at: datetime = Field(
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),  # initial value
            "onupdate": func.now(),  # Set value on UPDATE
        },
    )

    created_by: Optional[int] = Field(
        default=None, nullable=True, foreign_key="users.id"
    )
    updated_by: Optional[int] = Field(
        default=None, nullable=True, foreign_key="users.id"
    )

