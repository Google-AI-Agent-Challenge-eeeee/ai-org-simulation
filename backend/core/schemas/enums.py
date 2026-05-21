"""HR-domain enums.

System-level enums (Environment, LLMMode, Role 등)은 ``backend.core.constants.enums``에 있고,
이 파일은 **HR 데이터셋의 값 도메인**만 정의한다.
"""

from enum import StrEnum


class Gender(StrEnum):
    FEMALE = "F"
    MALE = "M"
    NON_DISCLOSED = "Non-disclosed"


class EmploymentStatus(StrEnum):
    ACTIVE = "재직"
    ON_LEAVE = "휴직"
    PRE_RESIGNATION = "퇴직예정"
    TERMINATED = "퇴직"


class EmploymentType(StrEnum):
    FULL_TIME = "정규직"
    CONTRACT = "계약직"
    INTERN = "인턴"


class Department(StrEnum):
    DESIGN = "디자인"
    DEVELOPMENT = "개발"
    QA = "QA 테스트"


class JobFamily(StrEnum):
    DESIGN = "Design"
    SOFTWARE_ENGINEERING = "Software Engineering"
    QA_ENGINEERING = "QA Engineering"
    INFRASTRUCTURE = "Infrastructure"


class JobLevel(StrEnum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"


class EducationLevel(StrEnum):
    ASSOCIATE = "전문학사"
    BACHELOR = "학사"
    MASTER = "석사"
    DOCTOR = "박사"


class PerformanceRating(StrEnum):
    """최근 성과 등급. S가 최상, D가 최하."""

    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class FetchStatus(StrEnum):
    """외부 소스(GitHub/Slack/Jira/Calendar) 수집 결과 상태.

    실패한 행도 DB에 남기고(원인 추적용), 분석/시뮬레이션 단계에서는 ``SUCCESS``만 필터링한다.
    """

    SUCCESS = "success"
    FAILED = "failed"
