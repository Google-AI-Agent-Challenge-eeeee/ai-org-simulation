"""CalendarActivity Pydantic schema.

직원 한 명의 특정 캘린더(보통 ``primary``) × 측정 구간 = 1행.
HR ↔ Calendar 조인 키는 ``google_email``.

CSV(`datasets/raw/calendar/`) 특이사항:
    - ``working_location_mix`` / ``meeting_provider_mix``: ``"home:30%;office:60%"`` →
      ``{"home": 0.30, "office": 0.60}`` (0~1 비율 dict).
    - ``active_hours``: ``"HH:MM-HH:MM"`` 형식 정규식 검증.
    - ``error_message`` 빈 문자열 → ``None``.
"""

import re
from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from backend.core.schemas.enums import FetchStatus

_ACTIVE_HOURS_RE = re.compile(r"^\d{2}:\d{2}-\d{2}:\d{2}$")


def _empty_to_none(value: Any) -> Any:  # noqa: ANN401
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _validate_active_hours(value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, str) and not _ACTIVE_HOURS_RE.match(value.strip()):
        raise ValueError(f"active_hours must match HH:MM-HH:MM, got {value!r}")
    return value


def _parse_percentage_mix(value: Any) -> Any:  # noqa: ANN401
    """``"home:30%;office:60%"`` → ``{"home": 0.3, "office": 0.6}``.

    Already-dict inputs pass through unchanged.
    """

    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        raise TypeError(f"Cannot coerce {type(value).__name__} into mix dict")

    result: dict[str, float] = {}
    for pair in value.split(";"):
        pair = pair.strip()
        if not pair:
            continue
        if ":" not in pair:
            raise ValueError(f"Mix entry missing ':' separator: {pair!r}")
        key, raw = pair.split(":", 1)
        raw = raw.strip().rstrip("%")
        try:
            num = float(raw)
        except ValueError as exc:
            raise ValueError(f"Mix value not numeric: {pair!r}") from exc
        result[key.strip()] = num / 100 if "%" in pair else num
    return result


OptionalStr = Annotated[str | None, BeforeValidator(_empty_to_none)]
ActiveHours = Annotated[str, BeforeValidator(_validate_active_hours)]
PercentageMix = Annotated[dict[str, float], BeforeValidator(_parse_percentage_mix)]


class CalendarActivity(BaseModel):
    """Single Google Calendar activity snapshot for one (user, calendar)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        extra="forbid",
    )

    google_email: str
    calendar_id: str

    measured_from: date
    measured_to: date

    event_count: int = Field(ge=0)
    meeting_count: int = Field(ge=0)
    total_meeting_minutes: int = Field(ge=0)
    avg_meeting_duration_minutes: float = Field(ge=0)
    all_day_event_count: int = Field(ge=0)

    active_hours: ActiveHours
    early_late_meeting_ratio: float = Field(ge=0, le=1)
    weekend_meeting_ratio: float = Field(ge=0, le=1)

    focus_time_count: int = Field(ge=0)
    focus_time_minutes: int = Field(ge=0)
    fragmented_calendar_score: float = Field(ge=0)
    no_meeting_block_count: int = Field(ge=0)

    organizer_event_count: int = Field(ge=0)
    attendee_event_count: int = Field(ge=0)
    organizer_ratio: float = Field(ge=0, le=1)
    attendee_count_avg: float = Field(ge=0)
    large_meeting_ratio: float = Field(ge=0, le=1)
    external_meeting_ratio: float = Field(ge=0, le=1)

    accepted_attendee_count: int = Field(ge=0)
    declined_attendee_count: int = Field(ge=0)
    tentative_attendee_count: int = Field(ge=0)
    no_response_ratio: float = Field(ge=0, le=1)

    recurring_event_count: int = Field(ge=0)
    recurring_meeting_ratio: float = Field(ge=0, le=1)
    busy_minutes: int = Field(ge=0)

    working_location_count: int = Field(ge=0)
    working_location_mix: PercentageMix = {}

    event_update_count: int = Field(ge=0)
    meeting_provider_mix: PercentageMix = {}

    fetched_at: datetime
    fetch_status: FetchStatus
    error_message: OptionalStr = None
