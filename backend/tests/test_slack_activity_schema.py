"""Validate the dummy Slack activity CSV against the Pydantic schema."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.core.schemas import (
    CollaborationStyle,
    Employee,
    FetchStatus,
    SlackActivity,
)
from backend.db.models import SlackActivity as SlackActivityOrm

SLACK_CSV_PATH = Path("datasets/raw/slack/slack_activity_dummy_100.csv")
HR_CSV_PATH = Path("datasets/raw/hr/employee_dummy_100.csv")
CSV_ENCODING = "utf-8-sig"


def _read_slack_rows() -> list[dict[str, str]]:
    with SLACK_CSV_PATH.open(encoding=CSV_ENCODING) as f:
        return list(csv.DictReader(f))


def test_csv_exists() -> None:
    assert SLACK_CSV_PATH.exists(), f"missing fixture: {SLACK_CSV_PATH}"


def test_all_rows_parse_successfully() -> None:
    rows = _read_slack_rows()
    assert rows, "slack CSV is empty"

    parsed = [SlackActivity.model_validate(row) for row in rows]
    assert len(parsed) == len(rows)


def test_semicolon_lists_are_split() -> None:
    rows = _read_slack_rows()
    multi_conv = next(row for row in rows if ";" in row["user_conversations"])
    parsed = SlackActivity.model_validate(multi_conv)

    assert isinstance(parsed.user_conversations, list)
    assert len(parsed.user_conversations) >= 2
    assert isinstance(parsed.top_collaborators, list)
    assert all(isinstance(x, str) and x for x in parsed.top_collaborators)


def test_collaboration_style_values_are_known() -> None:
    rows = _read_slack_rows()
    parsed_styles = {SlackActivity.model_validate(row).collaboration_style for row in rows}

    known = set(CollaborationStyle)
    assert parsed_styles <= known, f"unexpected styles: {parsed_styles - known}"


def test_slack_user_ids_join_with_hr_dataset() -> None:
    with HR_CSV_PATH.open(encoding=CSV_ENCODING) as f:
        hr_slack_ids = {Employee.model_validate(row).slack_user_id for row in csv.DictReader(f)}

    slack_ids = {row["slack_user_id"] for row in _read_slack_rows()}
    orphans = slack_ids - hr_slack_ids
    assert not orphans, f"Slack rows reference unknown employees: {orphans}"


def test_active_hours_format_rejects_garbage() -> None:
    base = _read_slack_rows()[0].copy()
    base["active_hours"] = "morning"

    with pytest.raises(ValidationError):
        SlackActivity.model_validate(base)


def test_empty_error_message_becomes_none() -> None:
    success_row = next(row for row in _read_slack_rows() if row["fetch_status"] == "success")
    parsed = SlackActivity.model_validate(success_row)

    assert parsed.fetch_status is FetchStatus.SUCCESS
    assert parsed.error_message is None


def test_orm_to_pydantic_conversion() -> None:
    orm = SlackActivityOrm(
        slack_user_id="U_TEST",
        measured_from=date(2026, 1, 1),
        measured_to=date(2026, 3, 31),
        accessible_conversations=10,
        user_conversations=["C-A", "C-B"],
        conversation_members=20,
        message_count=100,
        message_events=100,
        thread_replies=20,
        mention_count=15,
        collaboration_frequency=40,
        top_collaborators=["U_X", "U_Y"],
        avg_response_time=80.5,
        communication_balance=1.0,
        active_hours="09:00-18:00",
        night_activity_ratio=0.05,
        multitasking_score=70.0,
        leadership_score=50.0,
        dependency_score=40.0,
        bottleneck_risk=30.0,
        collaboration_style="connector",
        autonomy_score=60.0,
        burnout_risk=20.0,
        decision_latency=12.0,
        slack_user_profile="id=U_TEST;name=test;email=test@example.com",
        slack_users=100,
        fetched_at=datetime(2026, 5, 22, 9, 0, tzinfo=UTC),
        fetch_status="success",
        error_message=None,
    )

    parsed = SlackActivity.model_validate(orm)
    assert parsed.slack_user_id == "U_TEST"
    assert parsed.collaboration_style is CollaborationStyle.CONNECTOR
    assert parsed.top_collaborators == ["U_X", "U_Y"]
