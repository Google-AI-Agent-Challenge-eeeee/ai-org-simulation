"""CalendarActivity repository.

한 사람이 여러 캘린더를 가질 수 있어 ``get_primary`` / ``list_for_user`` 두 가지
조회 메서드를 함께 둔다. (Slack/Jira와 다른 점.)
"""

from collections.abc import Iterable, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.db.models.calendar_activity import CalendarActivity


class CalendarActivityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, google_email: str, calendar_id: str = "primary") -> CalendarActivity | None:
        """Lookup by ``(google_email, calendar_id)`` UNIQUE business key."""

        stmt = select(CalendarActivity).where(
            CalendarActivity.google_email == google_email,
            CalendarActivity.calendar_id == calendar_id,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def list_for_user(self, google_email: str) -> Sequence[CalendarActivity]:
        """Return all calendars belonging to one user."""

        stmt = (
            select(CalendarActivity)
            .where(CalendarActivity.google_email == google_email)
            .order_by(CalendarActivity.calendar_id)
        )
        return self._session.execute(stmt).scalars().all()

    def list_all(self) -> Sequence[CalendarActivity]:
        stmt = select(CalendarActivity).order_by(
            CalendarActivity.google_email, CalendarActivity.calendar_id
        )
        return self._session.execute(stmt).scalars().all()

    def list_paged(
        self,
        *,
        limit: int,
        offset: int,
        google_email: str | None = None,
    ) -> Sequence[CalendarActivity]:
        stmt = self._filtered_select(google_email)
        stmt = (
            stmt.order_by(CalendarActivity.google_email, CalendarActivity.calendar_id)
            .limit(limit)
            .offset(offset)
        )
        return self._session.execute(stmt).scalars().all()

    def count_filtered(self, *, google_email: str | None = None) -> int:
        stmt = self._filtered_select(google_email)
        return self._session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    @staticmethod
    def _filtered_select(google_email: str | None) -> Select[tuple[CalendarActivity]]:
        stmt = select(CalendarActivity)
        if google_email is not None:
            stmt = stmt.where(CalendarActivity.google_email == google_email)
        return stmt

    def count(self) -> int:
        return self._session.execute(
            select(func.count()).select_from(CalendarActivity)
        ).scalar_one()

    def add(self, activity: CalendarActivity) -> CalendarActivity:
        self._session.add(activity)
        self._session.flush()
        return activity

    def add_many(self, activities: Iterable[CalendarActivity]) -> None:
        self._session.add_all(list(activities))
        self._session.flush()
