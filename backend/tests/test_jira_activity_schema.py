"""Validate the dummy Jira activity CSV against the Pydantic schema."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.core.schemas import Employee, FetchStatus, JiraActivity
from backend.db.models import JiraActivity as JiraActivityOrm

JIRA_CSV_PATH = Path("datasets/raw/jira/jira_activity_dummy_100.csv")
HR_CSV_PATH = Path("datasets/raw/hr/employee_dummy_100.csv")
CSV_ENCODING = "utf-8-sig"


def _read_jira_rows() -> list[dict[str, str]]:
    with JIRA_CSV_PATH.open(encoding=CSV_ENCODING) as f:
        return list(csv.DictReader(f))


def test_csv_exists() -> None:
    assert JIRA_CSV_PATH.exists(), f"missing fixture: {JIRA_CSV_PATH}"


def test_all_rows_parse_successfully() -> None:
    rows = _read_jira_rows()
    assert rows, "jira CSV is empty"
    parsed = [JiraActivity.model_validate(row) for row in rows]
    assert len(parsed) == len(rows)


def test_percentage_mix_is_parsed_to_ratio_dict() -> None:
    """``"Bug:16%;Task:84%"`` → ``{"Bug": 0.16, "Task": 0.84}`` with sums near 1.0."""

    rows = _read_jira_rows()
    parsed = JiraActivity.model_validate(rows[0])

    assert isinstance(parsed.issue_type_mix, dict)
    assert parsed.issue_type_mix
    assert all(0.0 <= v <= 1.0 for v in parsed.issue_type_mix.values())
    # Mixes should roughly sum to 1.0 (allow rounding slack).
    assert abs(sum(parsed.issue_type_mix.values()) - 1.0) < 0.05
    assert abs(sum(parsed.priority_mix.values()) - 1.0) < 0.05


def test_sprint_participation_split_on_semicolon() -> None:
    rows = _read_jira_rows()
    multi_sprint = next(row for row in rows if ";" in row["sprint_participation"])
    parsed = JiraActivity.model_validate(multi_sprint)

    assert isinstance(parsed.sprint_participation, list)
    assert len(parsed.sprint_participation) >= 2
    assert all(s.startswith("SPR-") for s in parsed.sprint_participation)


def test_jira_ids_join_with_hr_dataset() -> None:
    with HR_CSV_PATH.open(encoding=CSV_ENCODING) as f:
        hr_jira_ids = {Employee.model_validate(row).jira_account_id for row in csv.DictReader(f)}

    jira_ids = {row["jira_account_id"] for row in _read_jira_rows()}
    orphans = jira_ids - hr_jira_ids
    assert not orphans, f"Jira rows reference unknown employees: {orphans}"


def test_empty_error_message_becomes_none() -> None:
    success_row = next(row for row in _read_jira_rows() if row["fetch_status"] == "success")
    parsed = JiraActivity.model_validate(success_row)
    assert parsed.fetch_status is FetchStatus.SUCCESS
    assert parsed.error_message is None


def test_malformed_mix_raises() -> None:
    base = _read_jira_rows()[0].copy()
    base["issue_type_mix"] = "Bug=16%"  # ':' 누락

    with pytest.raises(ValidationError):
        JiraActivity.model_validate(base)


def test_orm_to_pydantic_conversion() -> None:
    orm = JiraActivityOrm(
        jira_account_id="jira-test",
        measured_from=date(2026, 1, 1),
        measured_to=date(2026, 3, 31),
        assigned_issue_count=10,
        reported_issue_count=4,
        completed_issue_count=8,
        issue_type_mix={"Bug": 0.2, "Task": 0.8},
        priority_mix={"High": 0.3, "Medium": 0.7},
        avg_cycle_time=7.5,
        overdue_issue_count=1,
        estimation_accuracy=1.05,
        worklog_hours=60.0,
        comment_count=20,
        avg_comment_response_time=12.0,
        collaboration_touchpoints=5,
        status_transition_count=30,
        avg_time_in_status=3.2,
        reopened_issue_count=0,
        scope_change_count=2,
        task_breakdown_count=4,
        sprint_participation=["SPR-2026-01", "SPR-2026-02"],
        sprint_completion_rate=0.85,
        context_switching_score=40.0,
        autonomy_score=70.0,
        ownership_score=80.0,
        bottleneck_risk=15.0,
        fetched_at=datetime(2026, 5, 22, 9, 0, tzinfo=UTC),
        fetch_status="success",
        error_message=None,
    )

    parsed = JiraActivity.model_validate(orm)
    assert parsed.jira_account_id == "jira-test"
    assert parsed.issue_type_mix == {"Bug": 0.2, "Task": 0.8}
    assert parsed.sprint_participation == ["SPR-2026-01", "SPR-2026-02"]
    assert parsed.fetch_status is FetchStatus.SUCCESS
