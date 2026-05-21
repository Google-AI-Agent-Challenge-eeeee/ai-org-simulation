"""SQLAlchemy engine + session factory.

Single source of truth for DB connectivity. Every consumer (FastAPI route,
script, repository test) should grab a session from here so we have one
process-wide engine + connection pool.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create the process-wide SQLAlchemy engine (cached)."""

    settings = get_settings()
    return create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
        future=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create the process-wide session factory bound to ``get_engine``."""

    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yields a session and guarantees ``close()``.

    Usage::

        @router.get("/employees")
        def list_employees(db: Session = Depends(get_db)) -> list[Employee]:
            ...
    """

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
