"""Shared FastAPI dependencies.

Routes ``Depends(...)`` these instead of importing from ``backend.db``
directly, so we have one place to swap session strategies (e.g. request-scoped
transaction, read-only replica) without touching every router.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db as _get_db


def get_db() -> Iterator[Session]:
    """Re-export of :func:`backend.db.session.get_db` for the API layer."""

    yield from _get_db()


DbSession = Annotated[Session, Depends(get_db)]
