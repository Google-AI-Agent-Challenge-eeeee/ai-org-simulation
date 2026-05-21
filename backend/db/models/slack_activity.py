"""``slack_activities`` table — one row per Slack user (current snapshot).

Design notes:
    - PK는 surrogate ``id`` (외부 시스템 ID에 우리 DB 무결성을 묶지 않기 위함).
    - ``slack_user_id``는 ``UNIQUE`` — "한 사용자당 한 행" 보장 (current snapshot 의미).
      나중에 시계열로 가고 싶다면 UNIQUE를 ``(slack_user_id, measured_from)`` 복합으로 바꾸면 됨.
    - HR FK는 일부러 안 검는다 (모든 직원이 Slack 계정 있는 건 아님).
    - List 컬럼들(``user_conversations``, ``top_collaborators``)은 Postgres
      ``TEXT[]``. SQLite는 ARRAY 미지원이므로 단위 테스트는 Postgres에서만 돈다.
"""

from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.models.base import Base


class SlackActivity(Base):
    __tablename__ = "slack_activities"
    __table_args__ = (UniqueConstraint("slack_user_id", name="uq_slack_activity_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    slack_user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    measured_from: Mapped[date] = mapped_column(Date, nullable=False)
    measured_to: Mapped[date] = mapped_column(Date, nullable=False)

    accessible_conversations: Mapped[int] = mapped_column(Integer, nullable=False)
    user_conversations: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    conversation_members: Mapped[int] = mapped_column(Integer, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False)
    message_events: Mapped[int] = mapped_column(Integer, nullable=False)
    thread_replies: Mapped[int] = mapped_column(Integer, nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, nullable=False)

    collaboration_frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    top_collaborators: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    avg_response_time: Mapped[float] = mapped_column(Float, nullable=False)
    communication_balance: Mapped[float] = mapped_column(Float, nullable=False)

    active_hours: Mapped[str] = mapped_column(String(16), nullable=False)
    night_activity_ratio: Mapped[float] = mapped_column(Float, nullable=False)

    multitasking_score: Mapped[float] = mapped_column(Float, nullable=False)
    leadership_score: Mapped[float] = mapped_column(Float, nullable=False)
    dependency_score: Mapped[float] = mapped_column(Float, nullable=False)
    bottleneck_risk: Mapped[float] = mapped_column(Float, nullable=False)
    collaboration_style: Mapped[str] = mapped_column(String(32), nullable=False)
    autonomy_score: Mapped[float] = mapped_column(Float, nullable=False)
    burnout_risk: Mapped[float] = mapped_column(Float, nullable=False)
    decision_latency: Mapped[float] = mapped_column(Float, nullable=False)

    slack_user_profile: Mapped[str] = mapped_column(Text, nullable=False)
    slack_users: Mapped[int] = mapped_column(Integer, nullable=False)

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SlackActivity {self.slack_user_id} {self.collaboration_style}>"
