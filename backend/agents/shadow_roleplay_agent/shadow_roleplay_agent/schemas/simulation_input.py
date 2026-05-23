"""Shadow_RolePlay_Agent Phase 0 — Input Schema

5개 input 타입 Pydantic 모델과 최종 병합 패킷(SimulationInputPacket)을 정의한다.

설계 원칙:
- 원천 Git/Jira/Slack/Calendar DB 컬럼을 직접 담지 않는다.
- 업무 signal(capacity, delivery, communication, collaboration)과
  evidence_refs(어떤 원천 컬럼에서 왔는지 참조 키)만 포함한다.
- 직원 이름은 그대로 사용한다.
  나이·성별·주소·학교·개인 프로필 등 민감 정보는 포함하지 않는다.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

# ──────────────────────────────────────────────
# 공용 Signal Enum
# ──────────────────────────────────────────────


class CapacitySignal(StrEnum):
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"


class CommunicationSignal(StrEnum):
    LOW_DELAY = "low_delay"  # avg_response_time < 30분
    MEDIUM_DELAY = "medium_delay"  # avg_response_time 30~90분
    HIGH_DELAY = "high_delay"  # avg_response_time > 90분


class DeliverySignal(StrEnum):
    STABLE = "stable"  # sprint_completion_rate >= 0.7 and reopened_issue_count <= 1
    VARIABLE = "variable"  # sprint_completion_rate 0.5~0.7 or reopened_issue_count 2~4
    UNSTABLE = "unstable"  # sprint_completion_rate < 0.5 or reopened_issue_count >= 5


class CollaborationStyle(StrEnum):
    """slack.collaboration_style 컬럼 값과 1:1 대응."""

    ASYNC_DEEP_WORKER = "async_deep_worker"
    CONNECTOR = "connector"
    FOCUSED_INDIVIDUAL = "focused_individual"
    RAPID_RESPONDER = "rapid_responder"
    REVIEW_HUB = "review_hub"


class FeaturePriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


# ──────────────────────────────────────────────
# Input 1: Requirements_List
# ──────────────────────────────────────────────


class Milestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    due_day: int = Field(ge=1, description="스프린트 시작일 기준 D+N")
    owner_role: str


class Feature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_id: str
    feature_name: str
    priority: FeaturePriority
    assigned_role: str
    tech_requirements: list[str]
    dependencies: list[str] = Field(default_factory=list, description="의존하는 feature_id 목록")
    estimated_days: int = Field(ge=1)
    risk_notes: str = ""


class ProjectTimeline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_sprint_days: int = Field(ge=1)
    milestones: list[Milestone]


class RequirementsList(BaseModel):
    """프로젝트 기능·역할·기술·일정·제약·리스크 정의.

    Shadow Agent의 project context 및 phase planning 기준이 된다.
    """

    model_config = ConfigDict(extra="forbid")

    project_id: str
    project_name: str
    project_summary: str
    required_roles: list[str]
    required_skills: list[str]
    features: list[Feature]
    timeline: ProjectTimeline
    constraints: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Input 2: Selected_Team_Record
# ──────────────────────────────────────────────


class TeamMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str
    employee_name: str
    assigned_role: str


class SelectedTeamRecord(BaseModel):
    """앞단 팀 추천 결과에서 선택된 팀 정보.

    Shadow Agent의 simulation 대상 팀을 정의한다.
    """

    model_config = ConfigDict(extra="forbid")

    team_id: str
    team_rank: int = Field(ge=1)
    team_fit_score: float = Field(ge=0, le=100)
    members: list[TeamMember] = Field(min_length=2)
    role_coverage_score: float = Field(ge=0.0, le=1.0)
    skill_coverage_score: float = Field(ge=0.0, le=1.0)
    availability_score: float = Field(ge=0.0, le=1.0)
    team_risk_flags: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Input 3: Employee_Fit_Profile_Snapshot
# ──────────────────────────────────────────────


class EmployeeFitProfileSnapshot(BaseModel):
    """팀원 1인의 업무 signal 요약 스냅샷.

    원천 DB 컬럼 값을 직접 담지 않고 signal 분류값과
    evidence_refs(원천 컬럼 참조 키)만 포함한다.
    """

    model_config = ConfigDict(extra="forbid")

    employee_id: str
    employee_name: str
    assigned_role: str

    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)

    capacity_signal: CapacitySignal
    communication_signal: CommunicationSignal
    delivery_signal: DeliverySignal

    # slack.collaboration_style 컬럼 값과 동일한 enum 사용
    collaboration_signal: CollaborationStyle

    risk_tags: list[str] = Field(default_factory=list)

    # 이 signal이 어떤 원천 컬럼에서 파생됐는지 추적용 참조 키
    # 예: ["jira.overdue_issue_count", "calendar.busy_minutes"]
    evidence_refs: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Input 4: Team_Risk_Summary
# ──────────────────────────────────────────────


class TeamRiskSummary(BaseModel):
    """팀 단위 리스크 요약.

    개인 점수가 아닌 팀 조합 수준의 병목·gap·리스크를 담는다.
    Shadow Agent의 scenario event 생성과 issue prior로 사용된다.
    """

    model_config = ConfigDict(extra="forbid")

    team_id: str
    risk_tags: list[str]

    # 각 risk 지표의 사전 확률값 (0~1)
    risk_prior_scores: dict[str, float] = Field(
        description="예: {'schedule_risk': 0.42, 'integration_risk': 0.63}"
    )

    # 업무 집중이 우려되는 팀원 이름 목록
    bottleneck_members: list[str] = Field(default_factory=list)

    # 시뮬레이션에서 반드시 다뤄야 할 핵심 의존성
    critical_dependencies: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Input 5: Evidence_Metadata
# ──────────────────────────────────────────────


class EvidenceMetadata(BaseModel):
    """risk signal이 어떤 원천 컬럼에서 왔는지 추적하는 메타데이터.

    issue/risk 판단 시 근거 제시와 설명 가능성 확보를 위해 사용된다.
    원천 DB의 실제 값을 담지 않고 컬럼 참조 키와 해석만 포함한다.
    """

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    employee_name: str
    risk_tag: str

    # 원천 컬럼 참조 키 (예: "jira.overdue_issue_count")
    source_column: str

    # 실제 값 대신 상대적 수준 표현 (예: "7건", "상위 20%")
    signal_value: str

    # 이 signal이 의미하는 리스크 해석 요약
    interpretation: str


# ──────────────────────────────────────────────
# Simulation Input Packet (Phase 1 산출물)
# ──────────────────────────────────────────────


class SimulationInputPacket(BaseModel):
    """Phase 1 Simulation_Input_Builder 산출물.

    5개 input을 하나로 병합한 simulation 실행 단위.
    이후 모든 모듈은 이 패킷을 기준으로 동작한다.
    """

    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    project_context: RequirementsList
    selected_team: SelectedTeamRecord
    member_snapshots: list[EmployeeFitProfileSnapshot] = Field(min_length=1)
    team_risk_summary: TeamRiskSummary
    evidence_metadata: list[EvidenceMetadata] = Field(default_factory=list)
