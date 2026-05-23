from __future__ import annotations

from dataclasses import dataclass

from backend.services.team_selector import TopTeamSelector


@dataclass
class EmployeeStub:
    employee_id: str
    employee_name: str
    job_category_code: str
    manager_id: str | None = None
    tenure_years: float = 5.0
    performance_score: float = 80.0
    kpi_score: float = 80.0
    competency_score: float = 80.0
    peer_review_score: float = 80.0
    manager_review_score: float = 80.0
    engagement_score: float = 80.0
    absence_days_12m: int = 2
    overtime_hours_12m: int = 40
    certifications_count: int = 1
    turnover_risk_score: float = 10.0
    github_id: str | None = "gh"
    slack_user_id: str | None = "slack"
    jira_account_id: str | None = "jira"
    google_email: str | None = "employee@example.com"


def test_top_team_selector_picks_unique_required_roles() -> None:
    employees = [
        EmployeeStub("E_PM", "Project Lead", "DS", manager_id=None, performance_score=92),
        EmployeeStub("E_BE", "Backend One", "BE", performance_score=91),
        EmployeeStub("E_WEB", "Frontend One", "WEB", performance_score=90),
        EmployeeStub("E_QA", "QA One", "QA", performance_score=89),
        EmployeeStub("E_INFRA", "Infra One", "Infra", performance_score=88),
    ]

    result = TopTeamSelector().select(
        employees,
        required_roles=[
            "PM",
            "Backend Developer",
            "Frontend Developer",
            "QA Engineer",
            "DevOps Engineer",
        ],
    )

    assert result is not None
    team = result.teams[0]
    assert team["team_id"] == "team_db_top_001"
    assert team["role_coverage_score"] == 1.0
    assert [member["assigned_role"] for member in team["members"]] == [
        "PM",
        "Backend Developer",
        "Frontend Developer",
        "QA Engineer",
        "DevOps Engineer",
    ]
    assert len({member["employee_id"] for member in team["members"]}) == 5


def test_top_team_selector_uses_fallback_member_for_missing_role() -> None:
    employees = [
        EmployeeStub("E_PM", "Project Lead", "DS", manager_id=None),
        EmployeeStub("E_BE", "Backend One", "BE"),
        EmployeeStub("E_WEB", "Frontend One", "WEB"),
    ]

    result = TopTeamSelector().select(
        employees,
        required_roles=["PM", "Backend Developer", "QA Engineer"],
    )

    assert result is not None
    team = result.teams[0]
    assert team["role_coverage_score"] < 1.0
    assert "role_gap" in team["team_risk_flags"]
    assert team["skill_gaps"] == ["QA Engineer: no exact job-category match"]


def test_top_team_selector_returns_none_without_employees() -> None:
    assert TopTeamSelector().select([]) is None
