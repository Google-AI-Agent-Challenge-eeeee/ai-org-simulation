"""``calendar_activities`` table — one row per (google_email, calendar_id) snapshot.

Design notes:
    - Surrogate ``id`` PK + ``UNIQUE(google_email, calendar_id)`` 복합 유니크.
      한 사람이 여러 캘린더(``primary`` + 공유)를 가질 수 있어 단일 컬럼이 아니다.
    - ``google_email``에 단독 INDEX 추가 — "이 사람의 모든 캘린더" 조회 패턴이 흔하다.
    - 두 분포 컬럼(``working_location_mix``, ``meeting_provider_mix``)은 Postgres ``JSONB``.
    - HR FK는 안 검 (모든 직원이 Google 계정 있는 건 아님).
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.models.base import Base


class CalendarActivity(Base):
    __tablename__ = "calendar_activities"
    __table_args__ = (
        UniqueConstraint("google_email", "calendar_id", name="uq_calendar_activity_user_calendar"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    google_email: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    calendar_id: Mapped[str] = mapped_column(String(128), nullable=False)

    measured_from: Mapped[date] = mapped_column(Date, nullable=False)
    measured_to: Mapped[date] = mapped_column(Date, nullable=False)

    event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    meeting_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_meeting_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_meeting_duration_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    all_day_event_count: Mapped[int] = mapped_column(Integer, nullable=False)

    active_hours: Mapped[str] = mapped_column(String(16), nullable=False)
    early_late_meeting_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    weekend_meeting_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    focus_time_count: Mapped[int] = mapped_column(Integer, nullable=False)
    focus_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    fragmented_calendar_score: Mapped[float] = mapped_column(Float, nullable=False)
    no_meeting_block_count: Mapped[int] = mapped_column(Integer, nullable=False)

    organizer_event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    attendee_event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    organizer_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    attendee_count_avg: Mapped[float] = mapped_column(Float, nullable=False)
    large_meeting_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    external_meeting_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    accepted_attendee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    declined_attendee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    tentative_attendee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    no_response_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    recurring_event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recurring_meeting_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    busy_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    working_location_count: Mapped[int] = mapped_column(Integer, nullable=False)
    working_location_mix: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    event_update_count: Mapped[int] = mapped_column(Integer, nullable=False)
    meeting_provider_mix: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CalendarActivity {self.google_email}/{self.calendar_id}>"
