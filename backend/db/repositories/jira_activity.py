"""JiraActivity repository — current-snapshot CRUD."""

from collections.abc import Iterable, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.db.models.jira_activity import JiraActivity


class JiraActivityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, jira_account_id: str) -> JiraActivity | None:
        """Lookup by external ``jira_account_id`` (UNIQUE business key)."""

        stmt = select(JiraActivity).where(JiraActivity.jira_account_id == jira_account_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> Sequence[JiraActivity]:
        stmt = select(JiraActivity).order_by(JiraActivity.jira_account_id)
        return self._session.execute(stmt).scalars().all()

    def list_paged(
        self,
        *,
        limit: int,
        offset: int,
        jira_account_id: str | None = None,
    ) -> Sequence[JiraActivity]:
        stmt = self._filtered_select(jira_account_id)
        stmt = stmt.order_by(JiraActivity.jira_account_id).limit(limit).offset(offset)
        return self._session.execute(stmt).scalars().all()

    def count_filtered(self, *, jira_account_id: str | None = None) -> int:
        stmt = self._filtered_select(jira_account_id)
        return self._session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    @staticmethod
    def _filtered_select(jira_account_id: str | None) -> Select[tuple[JiraActivity]]:
        stmt = select(JiraActivity)
        if jira_account_id is not None:
            stmt = stmt.where(JiraActivity.jira_account_id == jira_account_id)
        return stmt

    def count(self) -> int:
        return self._session.execute(select(func.count()).select_from(JiraActivity)).scalar_one()

    def add(self, activity: JiraActivity) -> JiraActivity:
        self._session.add(activity)
        self._session.flush()
        return activity

    def add_many(self, activities: Iterable[JiraActivity]) -> None:
        self._session.add_all(list(activities))
        self._session.flush()
