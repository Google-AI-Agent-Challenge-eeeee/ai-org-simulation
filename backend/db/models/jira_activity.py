"""``jira_activities`` table — one row per Jira user (current snapshot).

Design notes:
    - Slack과 동일한 패턴: surrogate ``id`` PK + ``jira_account_id`` UNIQUE+INDEX.
    - ``issue_type_mix``, ``priority_mix``는 Postgres ``JSONB``로 저장 (예:
      ``{"Bug": 0.16, "Design Task": 0.48}``). JSONB는 인덱스/연산자가 풍부해서
      추후 "Bug 비율 30% 이상" 같은 쿼리가 자연스럽다.
    - ``sprint_participation``은 ``TEXT[]``.
    - HR FK는 안 검 (모든 직원이 Jira 계정 있는 건 아님).
"""

from datetime import date, datetime
from typing import Any

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.models.base import Base


class JiraActivity(Base):
    __tablename__ = "jira_activities"
    __table_args__ = (UniqueConstraint("jira_account_id", name="uq_jira_activity_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    jira_account_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    measured_from: Mapped[date] = mapped_column(Date, nullable=False)
    measured_to: Mapped[date] = mapped_column(Date, nullable=False)

    assigned_issue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reported_issue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_issue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_type_mix: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    priority_mix: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    avg_cycle_time: Mapped[float] = mapped_column(Float, nullable=False)
    overdue_issue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    estimation_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    worklog_hours: Mapped[float] = mapped_column(Float, nullable=False)

    comment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_comment_response_time: Mapped[float] = mapped_column(Float, nullable=False)
    collaboration_touchpoints: Mapped[int] = mapped_column(Integer, nullable=False)

    status_transition_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_time_in_status: Mapped[float] = mapped_column(Float, nullable=False)
    reopened_issue_count: Mapped[int] = mapped_column(Integer, nullable=False)
    scope_change_count: Mapped[int] = mapped_column(Integer, nullable=False)
    task_breakdown_count: Mapped[int] = mapped_column(Integer, nullable=False)

    sprint_participation: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    sprint_completion_rate: Mapped[float] = mapped_column(Float, nullable=False)

    context_switching_score: Mapped[float] = mapped_column(Float, nullable=False)
    autonomy_score: Mapped[float] = mapped_column(Float, nullable=False)
    ownership_score: Mapped[float] = mapped_column(Float, nullable=False)
    bottleneck_risk: Mapped[float] = mapped_column(Float, nullable=False)

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<JiraActivity {self.jira_account_id}>"
