"""Declarative base for all ORM models.

Kept in its own module so importing ``Base`` never triggers loading of
concrete model files (avoids accidental circular imports).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide declarative base."""
