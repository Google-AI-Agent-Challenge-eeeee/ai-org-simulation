"""GitHub activity repository — CRUD over ``github_activities``.

Same conventions as ``EmployeeRepository``: takes a session, never commits.
"""

from collections.abc import Iterable, Sequence

from sqlalchemy import Select, func, select
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

    def list_paged(
        self,
        *,
        limit: int,
        offset: int,
        github_id: str | None = None,
    ) -> Sequence[GithubActivity]:
        stmt = self._filtered_select(github_id)
        stmt = (
            stmt.order_by(GithubActivity.github_id, GithubActivity.measured_from.desc())
            .limit(limit)
            .offset(offset)
        )
        return self._session.execute(stmt).scalars().all()

    def count_filtered(self, *, github_id: str | None = None) -> int:
        stmt = self._filtered_select(github_id)
        return self._session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    @staticmethod
    def _filtered_select(github_id: str | None) -> Select[tuple[GithubActivity]]:
        stmt = select(GithubActivity)
        if github_id is not None:
            stmt = stmt.where(GithubActivity.github_id == github_id)
        return stmt

    def count(self) -> int:
        return self._session.execute(select(func.count()).select_from(GithubActivity)).scalar_one()

    def add(self, activity: GithubActivity) -> GithubActivity:
        self._session.add(activity)
        self._session.flush()
        return activity

    def add_many(self, activities: Iterable[GithubActivity]) -> None:
        self._session.add_all(list(activities))
        self._session.flush()
