"""Database layer.

Modules:
    - ``session``: SQLAlchemy engine, session factory, FastAPI ``Depends`` helper.
    - ``models``: SQLAlchemy ORM models (one file per domain table).
    - ``repositories``: Thin CRUD wrappers around models for service-layer use.
    - ``migrations``: Alembic migration environment (managed via ``just db-*``).
"""
