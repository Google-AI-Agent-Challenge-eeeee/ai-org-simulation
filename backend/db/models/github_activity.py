"""``github_activities`` table — append-only snapshot per (employee, window).

Design notes:
    - ``id``는 surrogate PK. (`github_id`, `measured_from`, `measured_to`) 조합은
      논리적 유니크라 unique constraint로 강제한다.
    - ``github_id``는 HR 테이블의 ``employees.github_id``와 조인되는 키지만,
      모든 직원에게 GitHub 계정이 있는 건 아니므로 ``employees`` PK 자체와는 매핑하지 않는다.
      따라서 FK는 걸지 않고 인덱스만 둔다 (조인은 가능, 무결성은 비강제).
    - ``contributed_repositories``는 Postgres ``TEXT[]`` 배열. SQLite에는 array 타입이
      없지만 ARRAY 컬럼은 dialect별로 알아서 처리되므로 운영은 Postgres 기준이고
      유닛 테스트는 String 단일 저장으로 한다.
"""

from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.models.base import Base


class GithubActivity(Base):
    __tablename__ = "github_activities"
    __table_args__ = (
        UniqueConstraint(
            "github_id",
            "measured_from",
            "measured_to",
            name="uq_github_activity_window",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    github_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    measured_from: Mapped[date] = mapped_column(Date, nullable=False)
    measured_to: Mapped[date] = mapped_column(Date, nullable=False)

    commit_count_3m: Mapped[int] = mapped_column(Integer, nullable=False)
    pr_count_3m: Mapped[int] = mapped_column(Integer, nullable=False)
    merged_pr_count_3m: Mapped[int] = mapped_column(Integer, nullable=False)
    closed_unmerged_pr_count_3m: Mapped[int] = mapped_column(Integer, nullable=False)
    repository_contribution_count: Mapped[int] = mapped_column(Integer, nullable=False)
    contributed_repositories: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<GithubActivity {self.github_id} {self.measured_from}~{self.measured_to}>"
