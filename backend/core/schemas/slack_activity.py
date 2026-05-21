"""SlackActivity Pydantic schema.

직원 한 명 × 한 측정 구간 = 1행 (PK는 ``slack_user_id``, GitHub과 달리 append-only 아님).
CSV(`datasets/raw/slack/`) 특이사항:

- ``user_conversations``, ``top_collaborators``는 ``;``로 구분된 문자열 → ``list[str]``
- ``error_message``는 성공 시 빈 문자열 → ``None``
- ``slack_user_profile``은 ``id=...;name=...;email=...`` 형태 inline 문자열.
  현 단계는 그대로 보존 (구조화 파싱은 LLM/뷰어 측에서 해석).
- ``active_hours``는 ``"HH:MM-HH:MM"`` 단일 구간 문자열. 검증은 형식만 가볍게.
"""

import re
from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from backend.core.schemas.enums import CollaborationStyle, FetchStatus

_ACTIVE_HOURS_RE = re.compile(r"^\d{2}:\d{2}-\d{2}:\d{2}$")


def _empty_to_none(value: Any) -> Any:  # noqa: ANN401
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _split_semicolon(value: Any) -> Any:  # noqa: ANN401
    """``"a;b;c"`` → ``["a", "b", "c"]``; passes lists through; empty → ``[]``."""

    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        return [part.strip() for part in value.split(";") if part.strip()]
    raise TypeError(f"Cannot coerce {type(value).__name__} into list")


def _validate_active_hours(value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, str) and not _ACTIVE_HOURS_RE.match(value.strip()):
        raise ValueError(f"active_hours must match HH:MM-HH:MM, got {value!r}")
    return value


OptionalStr = Annotated[str | None, BeforeValidator(_empty_to_none)]
SemicolonList = Annotated[list[str], BeforeValidator(_split_semicolon)]
ActiveHours = Annotated[str, BeforeValidator(_validate_active_hours)]


class SlackActivity(BaseModel):
    """Single Slack activity snapshot per employee."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        extra="forbid",
    )

    slack_user_id: str

    measured_from: date
    measured_to: date

    accessible_conversations: int = Field(ge=0)
    user_conversations: SemicolonList = []
    conversation_members: int = Field(ge=0)
    message_count: int = Field(ge=0)
    message_events: int = Field(ge=0)
    thread_replies: int = Field(ge=0)
    mention_count: int = Field(ge=0)

    collaboration_frequency: int = Field(ge=0)
    top_collaborators: SemicolonList = []
    avg_response_time: float = Field(ge=0)
    communication_balance: float = Field(ge=0)

    active_hours: ActiveHours
    night_activity_ratio: float = Field(ge=0, le=1)

    multitasking_score: float = Field(ge=0)
    leadership_score: float = Field(ge=0)
    dependency_score: float = Field(ge=0)
    bottleneck_risk: float = Field(ge=0)
    collaboration_style: CollaborationStyle
    autonomy_score: float = Field(ge=0)
    burnout_risk: float = Field(ge=0)
    decision_latency: float = Field(ge=0)

    slack_user_profile: str
    slack_users: int = Field(ge=0)

    fetched_at: datetime
    fetch_status: FetchStatus
    error_message: OptionalStr = None
