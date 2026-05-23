"""Rule-based Top 1 team selector over HR employees.

This is intentionally a temporary ranking layer, not the final matching model.
It makes the MVP use real seeded employees while keeping the scoring surface
small enough to replace with EmployeeEvaluation later.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

DEFAULT_REQUIRED_ROLES = [
    "PM",
    "Backend Developer",
    "Frontend Developer",
    "QA Engineer",
    "DevOps Engineer",
]

ROLE_COLORS: dict[str, str] = {
    "PM": "bg-purple-500",
    "BE": "bg-blue-600",
    "WEB": "bg-cyan-500",
    "iOS": "bg-slate-500",
    "Android": "bg-green-600",
    "Infra": "bg-orange-500",
    "QA": "bg-amber-600",
    "DS": "bg-pink-500",
}


class EmployeeLike(Protocol):
    employee_id: str
    employee_name: str
    manager_id: str | None
    job_category_code: str
    tenure_years: float
    performance_score: float
    kpi_score: float
    competency_score: float
    peer_review_score: float
    manager_review_score: float
    engagement_score: float
    absence_days_12m: int
    overtime_hours_12m: int
    certifications_count: int
    turnover_risk_score: float
    github_id: str | None
    slack_user_id: str | None
    jira_account_id: str | None
    google_email: str | None


@dataclass(frozen=True)
class _Selection:
    employee: EmployeeLike
    assigned_role: str
    exact_role_match: bool
    score: float


@dataclass(frozen=True)
class TeamSelectionResult:
    total_combinations: int
    teams: list[dict]


class TopTeamSelector:
    """Pick one recommended team from available employees using transparent rules."""

    def select(
        self,
        employees: Sequence[EmployeeLike],
        *,
        required_roles: Sequence[str] | None = None,
    ) -> TeamSelectionResult | None:
        if not employees:
            return None

        roles = _normalize_required_roles(required_roles)
        selections = self._select_members(employees, roles)
        if len(selections) < 2:
            return None

        role_coverage = sum(selection.exact_role_match for selection in selections) / len(roles)
        skill_coverage = _skill_coverage(selections)
        availability = _availability_score(selections)
        individual_fit = sum(selection.score for selection in selections) / len(selections)
        team_fit = round(
            100
            * (
                individual_fit * 0.45
                + role_coverage * 0.25
                + skill_coverage * 0.15
                + availability * 0.15
            ),
            1,
        )

        return TeamSelectionResult(
            total_combinations=_estimate_total_combinations(employees, roles),
            teams=[
                {
                    "team_id": "team_db_top_001",
                    "team_name": "DB Top Recommendation",
                    "team_rank": 1,
                    "team_fit_score": team_fit,
                    "role_coverage_score": round(role_coverage, 2),
                    "skill_coverage_score": round(skill_coverage, 2),
                    "availability_score": round(availability, 2),
                    "team_risk_flags": _risk_flags(selections, role_coverage, availability),
                    "badges": ["DB employees", "Rule-based", "Top 1"],
                    "rationale": (
                        "Selected from seeded employees using role coverage, HR performance "
                        "signals, availability, and tool account coverage."
                    ),
                    "skill_gaps": _skill_gaps(selections),
                    "members": [_team_member(selection) for selection in selections],
                }
            ],
        )

    def _select_members(
        self,
        employees: Sequence[EmployeeLike],
        roles: Sequence[str],
    ) -> list[_Selection]:
        selected: list[_Selection] = []
        used_employee_ids: set[str] = set()

        for role in roles:
            candidates = [
                employee
                for employee in employees
                if employee.employee_id not in used_employee_ids and _matches_role(employee, role)
            ]
            exact_role_match = True
            if not candidates:
                candidates = [
                    employee
                    for employee in employees
                    if employee.employee_id not in used_employee_ids
                ]
                exact_role_match = False
            if not candidates:
                break

            employee = max(candidates, key=_employee_fit_score)
            used_employee_ids.add(employee.employee_id)
            selected.append(
                _Selection(
                    employee=employee,
                    assigned_role=role,
                    exact_role_match=exact_role_match,
                    score=_employee_fit_score(employee),
                )
            )

        return selected


def _normalize_required_roles(required_roles: Sequence[str] | None) -> list[str]:
    raw_roles = list(required_roles or [])
    if not raw_roles:
        raw_roles = DEFAULT_REQUIRED_ROLES
    if not any(_role_key(role) == "PM" for role in raw_roles):
        raw_roles.insert(0, "PM")

    normalized: list[str] = []
    seen: set[str] = set()
    for role in raw_roles:
        display_role = _display_role(role)
        key = display_role.casefold()
        if key not in seen:
            normalized.append(display_role)
            seen.add(key)
    return normalized[:5]


def _display_role(role: str) -> str:
    key = _role_key(role)
    return {
        "PM": "PM",
        "BE": "Backend Developer",
        "WEB": "Frontend Developer",
        "Infra": "DevOps Engineer",
        "QA": "QA Engineer",
        "iOS": "iOS Developer",
        "Android": "Android Developer",
        "DS": "Data Scientist",
        "Mobile": "Mobile Developer",
    }.get(key, role or "Team Member")


def _role_key(role: str) -> str:
    normalized = role.strip().casefold()
    if normalized in {"pm", "project manager", "product manager"}:
        return "PM"
    if "backend" in normalized or normalized == "be":
        return "BE"
    if "frontend" in normalized or "front-end" in normalized or normalized in {"web", "fe"}:
        return "WEB"
    if "devops" in normalized or "infra" in normalized or "sre" in normalized:
        return "Infra"
    if "qa" in normalized or "quality" in normalized or "test" in normalized:
        return "QA"
    if "ios" in normalized:
        return "iOS"
    if "android" in normalized:
        return "Android"
    if "mobile" in normalized:
        return "Mobile"
    if "data" in normalized or "design" in normalized:
        return "DS"
    return role.strip()


def _matches_role(employee: EmployeeLike, role: str) -> bool:
    role_key = _role_key(role)
    job_code = employee.job_category_code
    if role_key == "PM":
        return employee.manager_id is None
    if role_key == "Mobile":
        return job_code in {"Mobile", "iOS", "Android"}
    return job_code == role_key


def _employee_fit_score(employee: EmployeeLike) -> float:
    performance = _bounded(employee.performance_score / 100)
    kpi = _bounded(employee.kpi_score / 100)
    competency = _bounded(employee.competency_score / 100)
    peer = _bounded(employee.peer_review_score / 100)
    manager = _bounded(employee.manager_review_score / 100)
    engagement = _bounded(employee.engagement_score / 100)
    tenure = _bounded(employee.tenure_years / 8)
    certification = _bounded(employee.certifications_count / 3)
    stability = _bounded(1 - employee.turnover_risk_score / 100)
    workload = _bounded(1 - employee.overtime_hours_12m / 240)
    attendance = _bounded(1 - employee.absence_days_12m / 20)

    return _bounded(
        performance * 0.24
        + kpi * 0.16
        + competency * 0.14
        + peer * 0.08
        + manager * 0.10
        + engagement * 0.10
        + tenure * 0.07
        + certification * 0.04
        + stability * 0.04
        + workload * 0.02
        + attendance * 0.01
    )


def _skill_coverage(selections: Sequence[_Selection]) -> float:
    if not selections:
        return 0.0
    coverage = []
    for selection in selections:
        employee = selection.employee
        available = sum(
            value is not None
            for value in (
                employee.github_id,
                employee.slack_user_id,
                employee.jira_account_id,
                employee.google_email,
            )
        )
        coverage.append(available / 4)
    return sum(coverage) / len(coverage)


def _availability_score(selections: Sequence[_Selection]) -> float:
    if not selections:
        return 0.0
    return sum(
        _bounded(
            1
            - selection.employee.absence_days_12m / 25
            - selection.employee.overtime_hours_12m / 360
            - selection.employee.turnover_risk_score / 250
        )
        for selection in selections
    ) / len(selections)


def _risk_flags(
    selections: Sequence[_Selection],
    role_coverage: float,
    availability: float,
) -> list[str]:
    flags: list[str] = []
    if role_coverage < 1:
        flags.append("role_gap")
    if availability < 0.65:
        flags.append("availability_risk")
    if any(selection.employee.overtime_hours_12m >= 160 for selection in selections):
        flags.append("workload_risk")
    if any(selection.employee.turnover_risk_score >= 30 for selection in selections):
        flags.append("turnover_risk")
    return flags[:4]


def _skill_gaps(selections: Sequence[_Selection]) -> list[str]:
    return [
        f"{selection.assigned_role}: no exact job-category match"
        for selection in selections
        if not selection.exact_role_match
    ]


def _team_member(selection: _Selection) -> dict[str, str]:
    employee = selection.employee
    role_key = _role_key(selection.assigned_role)
    return {
        "employee_id": employee.employee_id,
        "employee_name": employee.employee_name,
        "assigned_role": selection.assigned_role,
        "initials": _initials(employee.employee_name),
        "color": ROLE_COLORS.get(role_key, "bg-zinc-500"),
    }


def _estimate_total_combinations(
    employees: Sequence[EmployeeLike],
    roles: Sequence[str],
) -> int:
    total = 1
    for role in roles:
        pool_size = sum(1 for employee in employees if _matches_role(employee, role))
        total *= max(1, pool_size)
    return total


def _initials(name: str) -> str:
    parts = name.split()
    if len(parts) <= 1:
        return name[:2]
    return "".join(part[:1] for part in parts[:2])


def _bounded(value: float) -> float:
    return min(1.0, max(0.0, value))
