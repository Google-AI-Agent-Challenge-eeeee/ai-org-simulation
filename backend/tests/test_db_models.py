"""Schema-level sanity tests for the ``employees`` ORM model.

Runs against an in-memory SQLite engine so the suite stays self-contained
(no docker, no fixtures). The schema-DDL path is identical to what Alembic
will emit, so this catches dumb regressions in column types / FK setup
before they reach Postgres.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.core.schemas import Employee as EmployeePydantic
from backend.db.models import Base, Employee


def _make_employee(**overrides: object) -> Employee:
    """Build a minimal-valid ORM ``Employee`` with sensible defaults."""

    defaults: dict[str, object] = {
        "employee_id": "E_TEST_001",
        "employee_name": "테스트 인물",
        "gender": "F",
        "birth_date": date(1990, 1, 1),
        "age": 36,
        "hire_date": date(2020, 1, 1),
        "tenure_years": 6.0,
        "employment_status": "재직",
        "employment_type": "정규직",
        "department": "개발",
        "team": "Platform",
        "job_family": "Software Engineering",
        "job_title": "Backend Engineer",
        "job_level": "L4",
        "manager_id": None,
        "work_location": "Seoul HQ",
        "education_level": "학사",
        "base_salary_krw": 80_000_000,
        "bonus_krw": 8_000_000,
        "last_performance_rating": "B",
        "performance_score": 85.0,
        "kpi_score": 90.0,
        "okr": "Ship Phase 2",
        "competency_score": 80.0,
        "peer_review_score": 80.0,
        "manager_review_score": 80.0,
        "self_review_score": 80.0,
        "promotion_eligible": True,
        "promotion_recommended": False,
        "last_promotion_date": None,
        "engagement_score": 70.0,
        "absence_days_12m": 3,
        "overtime_hours_12m": 40,
        "training_hours_12m": 24,
        "certifications_count": 1,
        "disciplinary_actions_12m": 0,
        "remote_work_days_12m": 120,
        "turnover_risk_score": 15.0,
        "github_id": None,
        "slack_user_id": None,
        "jira_account_id": None,
        "google_calendar_id": None,
    }
    defaults.update(overrides)
    return Employee(**defaults)


@pytest.fixture
def session() -> Session:
    """Fresh in-memory SQLite session per test."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_create_and_fetch_employee(session: Session) -> None:
    employee = _make_employee()
    session.add(employee)
    session.commit()

    fetched = session.get(Employee, "E_TEST_001")
    assert fetched is not None
    assert fetched.employee_name == "테스트 인물"
    assert fetched.promotion_eligible is True
    assert fetched.last_promotion_date is None


def test_manager_self_reference(session: Session) -> None:
    boss = _make_employee(employee_id="E_BOSS", employee_name="보스")
    underling = _make_employee(
        employee_id="E_UNDER",
        employee_name="언더링",
        manager_id="E_BOSS",
    )
    session.add_all([boss, underling])
    session.commit()

    fetched = session.get(Employee, "E_UNDER")
    assert fetched is not None
    assert fetched.manager is not None
    assert fetched.manager.employee_id == "E_BOSS"
    assert fetched.manager.reports[0].employee_id == "E_UNDER"


def test_orm_to_pydantic_conversion(session: Session) -> None:
    """``Pydantic.Employee.model_validate`` should accept an ORM row directly."""

    orm = _make_employee()
    session.add(orm)
    session.commit()

    fetched = session.get(Employee, "E_TEST_001")
    pydantic_model = EmployeePydantic.model_validate(fetched)

    assert pydantic_model.employee_id == "E_TEST_001"
    assert pydantic_model.gender.value == "F"
    assert pydantic_model.promotion_eligible is True
