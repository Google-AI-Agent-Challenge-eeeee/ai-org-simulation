"""Validate the dummy Google Calendar activity CSV against the Pydantic schema."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.core.schemas import CalendarActivity, Employee, FetchStatus
from backend.db.models import CalendarActivity as CalendarActivityOrm

CAL_CSV_PATH = Path("datasets/raw/calendar/google_calendar_activity_dummy_100.csv")
HR_CSV_PATH = Path("datasets/raw/hr/employee_dummy_100.csv")
CSV_ENCODING = "utf-8-sig"


def _read_cal_rows() -> list[dict[str, str]]:
    with CAL_CSV_PATH.open(encoding=CSV_ENCODING) as f:
        return list(csv.DictReader(f))


def test_csv_exists() -> None:
    assert CAL_CSV_PATH.exists(), f"missing fixture: {CAL_CSV_PATH}"


def test_all_rows_parse_successfully() -> None:
    rows = _read_cal_rows()
    assert rows, "calendar CSV is empty"
    parsed = [CalendarActivity.model_validate(row) for row in rows]
    assert len(parsed) == len(rows)


def test_percentage_mix_columns_parse_to_ratio_dict() -> None:
    rows = _read_cal_rows()
    parsed = CalendarActivity.model_validate(rows[0])

    assert isinstance(parsed.working_location_mix, dict)
    assert isinstance(parsed.meeting_provider_mix, dict)
    # location keys are subset of expected set
    assert set(parsed.working_location_mix.keys()) <= {"home", "office", "other"}
    assert all(0.0 <= v <= 1.0 for v in parsed.working_location_mix.values())
    assert abs(sum(parsed.working_location_mix.values()) - 1.0) < 0.05
    assert abs(sum(parsed.meeting_provider_mix.values()) - 1.0) < 0.05


def test_calendar_id_defaults_to_primary_in_dummy() -> None:
    rows = _read_cal_rows()
    assert {row["calendar_id"] for row in rows} == {"primary"}


def test_google_emails_join_with_hr_dataset() -> None:
    with HR_CSV_PATH.open(encoding=CSV_ENCODING) as f:
        hr_emails = {Employee.model_validate(row).google_email for row in csv.DictReader(f)}

    cal_emails = {row["google_email"] for row in _read_cal_rows()}
    orphans = cal_emails - hr_emails
    assert not orphans, f"Calendar rows reference unknown employees: {orphans}"


def test_active_hours_format_rejects_garbage() -> None:
    base = _read_cal_rows()[0].copy()
    base["active_hours"] = "morning"

    with pytest.raises(ValidationError):
        CalendarActivity.model_validate(base)


def test_empty_error_message_becomes_none() -> None:
    success_row = next(row for row in _read_cal_rows() if row["fetch_status"] == "success")
    parsed = CalendarActivity.model_validate(success_row)
    assert parsed.fetch_status is FetchStatus.SUCCESS
    assert parsed.error_message is None


def test_orm_to_pydantic_conversion() -> None:
    orm = CalendarActivityOrm(
        google_email="test@example.com",
        calendar_id="primary",
        measured_from=date(2026, 1, 1),
        measured_to=date(2026, 3, 31),
        event_count=100,
        meeting_count=60,
        total_meeting_minutes=1800,
        avg_meeting_duration_minutes=30.0,
        all_day_event_count=5,
        active_hours="09:00-18:00",
        early_late_meeting_ratio=0.05,
        weekend_meeting_ratio=0.02,
        focus_time_count=3,
        focus_time_minutes=300,
        fragmented_calendar_score=60.0,
        no_meeting_block_count=10,
        organizer_event_count=20,
        attendee_event_count=40,
        organizer_ratio=0.33,
        attendee_count_avg=5.0,
        large_meeting_ratio=0.1,
        external_meeting_ratio=0.15,
        accepted_attendee_count=30,
        declined_attendee_count=5,
        tentative_attendee_count=2,
        no_response_ratio=0.1,
        recurring_event_count=20,
        recurring_meeting_ratio=0.3,
        busy_minutes=3000,
        working_location_count=30,
        working_location_mix={"home": 0.5, "office": 0.5},
        event_update_count=10,
        meeting_provider_mix={"Google Meet": 0.7, "Zoom": 0.3},
        fetched_at=datetime(2026, 5, 22, 9, 0, tzinfo=UTC),
        fetch_status="success",
        error_message=None,
    )

    parsed = CalendarActivity.model_validate(orm)
    assert parsed.google_email == "test@example.com"
    assert parsed.calendar_id == "primary"
    assert parsed.working_location_mix == {"home": 0.5, "office": 0.5}
    assert parsed.meeting_provider_mix == {"Google Meet": 0.7, "Zoom": 0.3}
    assert parsed.fetch_status is FetchStatus.SUCCESS
