"""SQLAlchemy ORM models.

Importing this package side-effect-registers every model on ``Base.metadata``
so Alembic's ``autogenerate`` can see them. Add new models here when created.
"""

from backend.db.models.base import Base
from backend.db.models.employee import Employee
from backend.db.models.github_activity import GithubActivity

__all__ = ["Base", "Employee", "GithubActivity"]
