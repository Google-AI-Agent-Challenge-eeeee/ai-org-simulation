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


class JobCategoryCode(StrEnum):
    """직무 카테고리 코드 — `department`보다 더 세분화된 실 업무 분류.

    `department`가 "어느 본부 소속인지"라면, `job_category_code`는 "어떤 기술 도메인인지"다.
    예: `department=개발`이면서 `job_category_code∈{BE, WEB, Android, iOS, Mobile, Infra}`
    조합이 가능하다.
    """

    DS = "DS"  # Design System / 디자인
    BE = "BE"  # Backend
    WEB = "WEB"  # Web frontend
    ANDROID = "Android"
    IOS = "iOS"
    MOBILE = "Mobile"  # 모바일 공통/교차 영역
    INFRA = "Infra"  # Infrastructure / DevOps / SRE
    QA = "QA"  # Quality Assurance


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


class CollaborationStyle(StrEnum):
    """Slack 메시지 패턴 기반 협업 성향 분류 (derived).

    LLM/룰 기반 분류기가 산출하며, 평가용 단독 사용보다는 다른 지표와 결합해서 해석해야 한다.
    """

    RAPID_RESPONDER = "rapid_responder"
    FOCUSED_INDIVIDUAL = "focused_individual"
    CONNECTOR = "connector"
    REVIEW_HUB = "review_hub"
    ASYNC_DEEP_WORKER = "async_deep_worker"
