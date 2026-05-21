import csv
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.core.schemas import Employee
from backend.core.schemas.enums import (
    Department,
    EmploymentStatus,
    EmploymentType,
    Gender,
    JobFamily,
    JobLevel,
    PerformanceRating,
)

CSV_PATH = Path("datasets/raw/hr/employee_dummy_100.csv")
# Excel-exported CSVs often start with a UTF-8 BOM; ``utf-8-sig`` strips it transparently
# so the first column name stays as ``employee_id`` (not ``\ufeffemployee_id``).
CSV_ENCODING = "utf-8-sig"


def _row_to_employee(row: dict[str, str]) -> Employee:
    return Employee.model_validate(row)


def test_csv_exists() -> None:
    assert CSV_PATH.exists(), f"HR CSV not found at {CSV_PATH}"


def test_all_rows_parse_successfully() -> None:
    with CSV_PATH.open(encoding=CSV_ENCODING) as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 100, "기대 행 수(100)와 다름"

    failures: list[tuple[int, str, str]] = []
    for idx, row in enumerate(rows, start=2):
        try:
            _row_to_employee(row)
        except Exception as exc:
            failures.append((idx, row.get("employee_id", "?"), str(exc)))

    if failures:
        msg = "\n".join(f"  - line {ln} ({eid}): {err}" for ln, eid, err in failures[:5])
        pytest.fail(f"{len(failures)} row(s) failed to parse:\n{msg}")


def test_employee_ids_are_unique() -> None:
    with CSV_PATH.open(encoding=CSV_ENCODING) as f:
        ids = [row["employee_id"] for row in csv.DictReader(f)]
    assert len(ids) == len(set(ids)), "중복된 employee_id 발견"


def test_manager_ids_reference_existing_employees() -> None:
    with CSV_PATH.open(encoding=CSV_ENCODING) as f:
        rows = list(csv.DictReader(f))

    all_ids = {row["employee_id"] for row in rows}
    invalid: list[tuple[str, str]] = []
    for row in rows:
        manager_id = (row.get("manager_id") or "").strip()
        if manager_id and manager_id not in all_ids:
            invalid.append((row["employee_id"], manager_id))

    assert invalid == [], (
        f"manager_id가 employees에 없음: {invalid[:5]}{' ...' if len(invalid) > 5 else ''}"
    )


def test_yn_string_converted_to_bool() -> None:
    base_row = _minimal_row()
    base_row["promotion_eligible"] = "Y"
    base_row["promotion_recommended"] = "n"

    emp = Employee.model_validate(base_row)
    assert emp.promotion_eligible is True
    assert emp.promotion_recommended is False


def test_empty_string_converted_to_none() -> None:
    base_row = _minimal_row()
    base_row["manager_id"] = ""
    base_row["last_promotion_date"] = ""
    base_row["github_id"] = ""

    emp = Employee.model_validate(base_row)
    assert emp.manager_id is None
    assert emp.last_promotion_date is None
    assert emp.github_id is None


def test_extra_column_rejected() -> None:
    base_row = _minimal_row()
    base_row["unexpected_column"] = "anything"

    with pytest.raises(ValidationError):
        Employee.model_validate(base_row)


def _minimal_row() -> dict[str, str]:
    return {
        "employee_id": "E20260999",
        "employee_name": "테스트",
        "gender": Gender.FEMALE.value,
        "birth_date": "1990-01-01",
        "age": "35",
        "hire_date": "2020-01-01",
        "tenure_years": "5.0",
        "employment_status": EmploymentStatus.ACTIVE.value,
        "employment_type": EmploymentType.FULL_TIME.value,
        "department": Department.DEVELOPMENT.value,
        "team": "백엔드",
        "job_family": JobFamily.SOFTWARE_ENGINEERING.value,
        "job_title": "백엔드 엔지니어",
        "job_level": JobLevel.L3.value,
        "manager_id": "E20260001",
        "work_location": "서울 본사",
        "education_level": "학사",
        "base_salary_krw": "60000000",
        "bonus_krw": "5000000",
        "last_performance_rating": PerformanceRating.A.value,
        "performance_score": "80.0",
        "kpi_score": "85.0",
        "okr": "테스트 목표",
        "competency_score": "80.0",
        "peer_review_score": "80.0",
        "manager_review_score": "80.0",
        "self_review_score": "80.0",
        "promotion_eligible": "Y",
        "promotion_recommended": "N",
        "last_promotion_date": "2023-01-01",
        "engagement_score": "75.0",
        "absence_days_12m": "2",
        "overtime_hours_12m": "30",
        "training_hours_12m": "20",
        "certifications_count": "1",
        "disciplinary_actions_12m": "0",
        "remote_work_days_12m": "40",
        "turnover_risk_score": "15.0",
        "github_id": "gh-test",
        "slack_user_id": "U-test",
        "jira_account_id": "jira-test",
        "google_calendar_id": "test@example.com",
    }


def test_minimal_row_constructs_expected_employee() -> None:
    emp = Employee.model_validate(_minimal_row())
    assert emp.employee_id == "E20260999"
    assert emp.gender is Gender.FEMALE
    assert emp.birth_date == date(1990, 1, 1)
    assert emp.department is Department.DEVELOPMENT
    assert emp.job_level is JobLevel.L3
