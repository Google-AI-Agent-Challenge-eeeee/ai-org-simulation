"""JiraActivity Pydantic schema.

직원 한 명 × 한 측정 구간 = 1행 (Slack과 동일한 current snapshot 패턴).

CSV(`datasets/raw/jira/`) 특이사항:
    - ``issue_type_mix`` / ``priority_mix``는 ``"Type:48%;Other:18%"`` 형식 문자열.
      ``BeforeValidator``가 ``{"Type": 0.48, "Other": 0.18}`` (0~1 비율 dict)로 변환.
    - ``sprint_participation``은 ``;``로 구분된 문자열 → ``list[str]``.
    - ``error_message`` 빈 문자열 → ``None``.
"""

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from backend.core.schemas.enums import FetchStatus


def _empty_to_none(value: Any) -> Any:  # noqa: ANN401
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _split_semicolon(value: Any) -> Any:  # noqa: ANN401
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        return [part.strip() for part in value.split(";") if part.strip()]
    raise TypeError(f"Cannot coerce {type(value).__name__} into list")


def _parse_percentage_mix(value: Any) -> Any:  # noqa: ANN401
    """``"Bug:16%;Task:84%"`` → ``{"Bug": 0.16, "Task": 0.84}``.

    Already-dict inputs (e.g. from ORM/JSON) are passed through unchanged.
    Values without ``%`` are accepted as raw floats too (forward compatible).
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
        # "16%" → 0.16; raw float (already 0~1) passes through if no '%' present.
        result[key.strip()] = num / 100 if "%" in pair else num
    return result


OptionalStr = Annotated[str | None, BeforeValidator(_empty_to_none)]
SemicolonList = Annotated[list[str], BeforeValidator(_split_semicolon)]
PercentageMix = Annotated[dict[str, float], BeforeValidator(_parse_percentage_mix)]


class JiraActivity(BaseModel):
    """Single Jira activity snapshot per employee."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        extra="forbid",
    )

    jira_account_id: str

    measured_from: date
    measured_to: date

    assigned_issue_count: int = Field(ge=0)
    reported_issue_count: int = Field(ge=0)
    completed_issue_count: int = Field(ge=0)
    issue_type_mix: PercentageMix = {}
    priority_mix: PercentageMix = {}

    avg_cycle_time: float = Field(ge=0)
    overdue_issue_count: int = Field(ge=0)
    estimation_accuracy: float = Field(ge=0)
    worklog_hours: float = Field(ge=0)

    comment_count: int = Field(ge=0)
    avg_comment_response_time: float = Field(ge=0)
    collaboration_touchpoints: int = Field(ge=0)

    status_transition_count: int = Field(ge=0)
    avg_time_in_status: float = Field(ge=0)
    reopened_issue_count: int = Field(ge=0)
    scope_change_count: int = Field(ge=0)
    task_breakdown_count: int = Field(ge=0)

    sprint_participation: SemicolonList = []
    # 스프린트 완료율 — 보통 0~1이지만 추가 이슈를 끌어 완료하면 1.0을 살짝 넘을 수 있다.
    sprint_completion_rate: float = Field(ge=0)

    context_switching_score: float = Field(ge=0)
    autonomy_score: float = Field(ge=0)
    ownership_score: float = Field(ge=0)
    bottleneck_risk: float = Field(ge=0)

    fetched_at: datetime
    fetch_status: FetchStatus
    error_message: OptionalStr = None
