"""SlackActivity repository — current-snapshot CRUD."""

from collections.abc import Iterable, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.db.models.slack_activity import SlackActivity


class SlackActivityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, slack_user_id: str) -> SlackActivity | None:
        """Lookup by external ``slack_user_id`` (the UNIQUE business key).

        PK is a surrogate ``id``, so we go through ``WHERE slack_user_id = ?``
        instead of ``Session.get``.
        """

        stmt = select(SlackActivity).where(SlackActivity.slack_user_id == slack_user_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> Sequence[SlackActivity]:
        stmt = select(SlackActivity).order_by(SlackActivity.slack_user_id)
        return self._session.execute(stmt).scalars().all()

    def list_paged(
        self,
        *,
        limit: int,
        offset: int,
        slack_user_id: str | None = None,
    ) -> Sequence[SlackActivity]:
        stmt = self._filtered_select(slack_user_id)
        stmt = stmt.order_by(SlackActivity.slack_user_id).limit(limit).offset(offset)
        return self._session.execute(stmt).scalars().all()

    def count_filtered(self, *, slack_user_id: str | None = None) -> int:
        stmt = self._filtered_select(slack_user_id)
        return self._session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    @staticmethod
    def _filtered_select(slack_user_id: str | None) -> Select[tuple[SlackActivity]]:
        stmt = select(SlackActivity)
        if slack_user_id is not None:
            stmt = stmt.where(SlackActivity.slack_user_id == slack_user_id)
        return stmt

    def count(self) -> int:
        return self._session.execute(select(func.count()).select_from(SlackActivity)).scalar_one()

    def add(self, activity: SlackActivity) -> SlackActivity:
        self._session.add(activity)
        self._session.flush()
        return activity

    def add_many(self, activities: Iterable[SlackActivity]) -> None:
        self._session.add_all(list(activities))
        self._session.flush()
