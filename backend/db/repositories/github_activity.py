"""GitHub activity repository — CRUD over ``github_activities``.

Same conventions as ``EmployeeRepository``: takes a session, never commits.
"""

from collections.abc import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.github_activity import GithubActivity


class GithubActivityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_user(self, github_id: str) -> Sequence[GithubActivity]:
        stmt = (
            select(GithubActivity)
            .where(GithubActivity.github_id == github_id)
            .order_by(GithubActivity.measured_from.desc())
        )
        return self._session.execute(stmt).scalars().all()

    def list_all(self) -> Sequence[GithubActivity]:
        stmt = select(GithubActivity).order_by(
            GithubActivity.github_id, GithubActivity.measured_from.desc()
        )
        return self._session.execute(stmt).scalars().all()

    def count(self) -> int:
        stmt = select(GithubActivity)
        return len(self._session.execute(stmt).scalars().all())

    def add(self, activity: GithubActivity) -> GithubActivity:
        self._session.add(activity)
        self._session.flush()
        return activity

    def add_many(self, activities: Iterable[GithubActivity]) -> None:
        self._session.add_all(list(activities))
        self._session.flush()
