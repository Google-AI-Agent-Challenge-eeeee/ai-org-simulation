"""SlackActivity repository — current-snapshot CRUD."""

from collections.abc import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models.slack_activity import SlackActivity


class SlackActivityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, slack_user_id: str) -> SlackActivity | None:
        return self._session.get(SlackActivity, slack_user_id)

    def list_all(self) -> Sequence[SlackActivity]:
        stmt = select(SlackActivity).order_by(SlackActivity.slack_user_id)
        return self._session.execute(stmt).scalars().all()

    def count(self) -> int:
        stmt = select(SlackActivity)
        return len(self._session.execute(stmt).scalars().all())

    def add(self, activity: SlackActivity) -> SlackActivity:
        self._session.add(activity)
        self._session.flush()
        return activity

    def add_many(self, activities: Iterable[SlackActivity]) -> None:
        self._session.add_all(list(activities))
        self._session.flush()
