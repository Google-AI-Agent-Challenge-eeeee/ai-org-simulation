"""Employee Pydantic schema.

CSV 직접 파싱과 향후 ORM 변환을 모두 지원하기 위해 ``Employee``는 다음을 보장한다:

- 빈 문자열은 ``None``으로 자동 변환 (`manager_id`, `last_promotion_date`, 툴 ID 등)
- ``"Y"``/``"N"`` 문자열은 ``bool``로 자동 변환 (`promotion_*`)
- ``from_attributes=True``로 SQLAlchemy 모델 → Pydantic 변환 가능
- ``extra="forbid"``로 CSV에 신규 컬럼이 들어오면 즉시 실패 (스키마 drift 감지)
"""

from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from backend.core.schemas.enums import (
    Department,
    EducationLevel,
    EmploymentStatus,
    EmploymentType,
    Gender,
    JobCategoryCode,
    PerformanceRating,
)


def _empty_to_none(value: Any) -> Any:  # noqa: ANN401
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _yn_to_bool(value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized == "Y":
            return True
        if normalized == "N":
            return False
    raise ValueError(f"Expected 'Y' or 'N', got {value!r}")


OptionalStr = Annotated[str | None, BeforeValidator(_empty_to_none)]
OptionalDate = Annotated[date | None, BeforeValidator(_empty_to_none)]
YesNoBool = Annotated[bool, BeforeValidator(_yn_to_bool)]


class Employee(BaseModel):
    """단일 직원 레코드. ``datasets/raw/hr/*.csv`` 한 줄 ≡ Employee 인스턴스 한 개."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        extra="forbid",
    )

    # 식별자
    employee_id: str

    # 기본 정보
    employee_name: str
    gender: Gender
    birth_date: date
    age: int = Field(ge=0, le=150)

    # 재직 정보
    hire_date: date
    tenure_years: float = Field(ge=0)
    employment_status: EmploymentStatus
    employment_type: EmploymentType

    # 조직/직무
    department: Department
    job_category_code: JobCategoryCode
    manager_id: OptionalStr = None

    # 근무 정보
    work_location: str

    # 역량/배경
    education_level: EducationLevel

    # 보상
    base_salary_krw: int = Field(ge=0)
    bonus_krw: int = Field(ge=0)

    # 성과/평가 — 일부 점수는 100% 초과 가능 (예: KPI 목표 초과 달성)
    last_performance_rating: PerformanceRating
    performance_score: float = Field(ge=0)
    kpi_score: float = Field(ge=0)
    competency_score: float = Field(ge=0)
    peer_review_score: float = Field(ge=0)
    manager_review_score: float = Field(ge=0)
    self_review_score: float = Field(ge=0)

    # 승진
    promotion_eligible: YesNoBool
    promotion_recommended: YesNoBool
    last_promotion_date: OptionalDate = None

    # 조직 상태
    engagement_score: float = Field(ge=0)

    # 근태
    absence_days_12m: int = Field(ge=0, le=366)
    overtime_hours_12m: int = Field(ge=0)

    # 교육/역량
    training_hours_12m: int = Field(ge=0)
    certifications_count: int = Field(ge=0)

    # 리스크
    disciplinary_actions_12m: int = Field(ge=0)
    remote_work_days_12m: int = Field(ge=0, le=366)
    turnover_risk_score: float = Field(ge=0)

    # 외부 툴 계정 ID (다른 raw DB와의 조인 키)
    github_id: OptionalStr = None
    slack_user_id: OptionalStr = None
    jira_account_id: OptionalStr = None
    google_email: OptionalStr = None  # Calendar 데이터셋과의 조인 키
