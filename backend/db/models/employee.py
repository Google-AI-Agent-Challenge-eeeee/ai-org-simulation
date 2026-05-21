"""``employees`` table — ORM model mirroring the HR Pydantic schema.

Conventions:
    - Columns map 1:1 to ``backend.core.schemas.Employee`` field names so
      ``Employee.model_validate(orm_obj)`` works without remapping.
    - Enum-valued columns are stored as ``String`` (not Postgres ENUM) so
      adding a new value never requires a migration. Validation lives in the
      Pydantic layer.
    - ``manager_id`` is a self-referential FK to ``employee_id`` (nullable).
"""

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.models.base import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String(32), primary_key=True)

    employee_name: Mapped[str] = mapped_column(String(64), nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)

    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    tenure_years: Mapped[float] = mapped_column(Float, nullable=False)
    employment_status: Mapped[str] = mapped_column(String(16), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(16), nullable=False)

    department: Mapped[str] = mapped_column(String(64), nullable=False)
    team: Mapped[str] = mapped_column(String(64), nullable=False)
    job_family: Mapped[str] = mapped_column(String(64), nullable=False)
    job_title: Mapped[str] = mapped_column(String(64), nullable=False)
    job_level: Mapped[str] = mapped_column(String(16), nullable=False)
    manager_id: Mapped[str | None] = mapped_column(
        String(32),
        ForeignKey("employees.employee_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    work_location: Mapped[str] = mapped_column(String(64), nullable=False)

    education_level: Mapped[str] = mapped_column(String(32), nullable=False)

    base_salary_krw: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_krw: Mapped[int] = mapped_column(Integer, nullable=False)

    last_performance_rating: Mapped[str] = mapped_column(String(8), nullable=False)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False)
    kpi_score: Mapped[float] = mapped_column(Float, nullable=False)
    okr: Mapped[str] = mapped_column(String(255), nullable=False)
    competency_score: Mapped[float] = mapped_column(Float, nullable=False)
    peer_review_score: Mapped[float] = mapped_column(Float, nullable=False)
    manager_review_score: Mapped[float] = mapped_column(Float, nullable=False)
    self_review_score: Mapped[float] = mapped_column(Float, nullable=False)

    promotion_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    promotion_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False)
    last_promotion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    engagement_score: Mapped[float] = mapped_column(Float, nullable=False)

    absence_days_12m: Mapped[int] = mapped_column(Integer, nullable=False)
    overtime_hours_12m: Mapped[int] = mapped_column(Integer, nullable=False)

    training_hours_12m: Mapped[int] = mapped_column(Integer, nullable=False)
    certifications_count: Mapped[int] = mapped_column(Integer, nullable=False)

    disciplinary_actions_12m: Mapped[int] = mapped_column(Integer, nullable=False)
    remote_work_days_12m: Mapped[int] = mapped_column(Integer, nullable=False)
    turnover_risk_score: Mapped[float] = mapped_column(Float, nullable=False)

    github_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    slack_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    jira_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    google_calendar_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Self-referential relationship — handy for traversing manager chains
    # without writing manual joins. ``remote_side`` tells SQLAlchemy that the
    # parent side of the relationship is the row whose PK matches ``manager_id``.
    manager: Mapped["Employee | None"] = relationship(
        "Employee",
        remote_side="Employee.employee_id",
        back_populates="reports",
    )
    reports: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="manager",
        cascade="save-update",
    )

    def __repr__(self) -> str:
        return f"<Employee {self.employee_id} {self.employee_name}>"
