"""Repository layer.

Repositories are thin, table-scoped CRUD wrappers. They:
    - Take a ``Session`` (do **not** create their own).
    - Return ORM instances; converting to Pydantic / DTO is the caller's job.
    - Never call ``session.commit()`` — the caller (route / service) owns the
      transaction boundary so we can compose multiple repo calls atomically.
"""

from backend.db.repositories.calendar_activity import CalendarActivityRepository
from backend.db.repositories.employee import EmployeeRepository
from backend.db.repositories.github_activity import GithubActivityRepository
from backend.db.repositories.jira_activity import JiraActivityRepository
from backend.db.repositories.slack_activity import SlackActivityRepository

__all__ = [
    "CalendarActivityRepository",
    "EmployeeRepository",
    "GithubActivityRepository",
    "JiraActivityRepository",
    "SlackActivityRepository",
]
