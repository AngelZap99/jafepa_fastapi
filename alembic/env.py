from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

import src.shared.models.register_models  # noqa: F401
from src.shared.database.database_config import engine


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = SQLModel.metadata


def _set_sqlalchemy_url_from_engine() -> None:
    # Alembic uses ConfigParser which treats `%` as interpolation markers.
    # SQLAlchemy URLs may contain percent-encoded sequences (e.g. `%40`) when
    # the password has special characters, so we must escape `%` as `%%`.
    url = engine.url.render_as_string(hide_password=False).replace("%", "%%")
    config.set_main_option("sqlalchemy.url", url)


def run_migrations_offline() -> None:
    _set_sqlalchemy_url_from_engine()
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _set_sqlalchemy_url_from_engine()

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
