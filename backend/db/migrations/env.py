"""Alembic migration environment.

Wires Alembic up to the project's settings + ORM metadata so that running
``alembic upgrade`` / ``alembic revision --autogenerate`` "just works" without
any URL duplication between ``alembic.ini`` and ``.env``.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.core.config.settings import get_settings

# Importing the ``models`` package side-effect-registers every model class on
# ``Base.metadata`` — required for ``--autogenerate`` to detect new tables.
from backend.db.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL to stdout)."""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to DB and apply)."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
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
