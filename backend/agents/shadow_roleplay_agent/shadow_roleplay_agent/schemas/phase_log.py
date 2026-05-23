"""Phase 7 산출물 스키마 — Phase Log

Phase_Log_Collector가 생성하는 구조화 로그.
Team_Simulation_Log.json의 기본 단위이며
Phase 8 Issue/Risk Evaluator의 입력이 된다.

io_schema.md §6 Phase Log Schema 기준.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class IssueSeverity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueStatus(StrEnum):
    CANDIDATE = "candidate"  # 아직 미확정
    CONFIRMED = "confirmed"  # Phase 8에서 확정
    INVALID = "invalid"  # evidence 없음 → 기각


class ParticipantTurnSummary(BaseModel):
    """phase log용 간결 발언 요약 — raw_dialogue가 아닌 구조화 요약."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    role: str
    observation: str
    concern: str
    dependency: str
    proposed_action: str
    evidence_refs_used: list[str] = Field(default_factory=list)
    is_valid: bool = True


class IssueCandidate(BaseModel):
    """concern 또는 unresolved_question에서 추출한 issue 후보.

    Phase 8에서 evidence + simulation log 교차 검증 후 확정 여부 결정.
    """

    model_config = ConfigDict(extra="forbid")

    issue_id: str
    issue_category: str  # rules.md §2 지표 중 하나
    description: str
    raised_by: str  # agent_id
    raised_in_phase: str
    trigger_source: list[str] = Field(default_factory=list)
    severity: IssueSeverity = IssueSeverity.MEDIUM
    status: IssueStatus = IssueStatus.CANDIDATE
    evidence_refs: list[str] = Field(default_factory=list)


class Decision(BaseModel):
    """phase에서 합의된 결정 사항."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str
    summary: str
    decided_by: str  # agent_id (주도 역할)
    phase: str


class ActionItem(BaseModel):
    """phase에서 도출된 액션 아이템."""

    model_config = ConfigDict(extra="forbid")

    action_id: str
    description: str
    owner_role: str
    phase: str
    priority: str = "medium"  # high / medium / low
    evidence_refs: list[str] = Field(default_factory=list)


class UnresolvedQuestion(BaseModel):
    """phase 종료 시 미해결로 남은 의존성 또는 질문."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    description: str
    raised_by: str
    phase: str
    risk_category: str


class PhaseScore(BaseModel):
    """phase별 사전 점수 — Phase 9 Score Calculator의 선행 시그널."""

    model_config = ConfigDict(extra="forbid")

    phase: str
    valid_turn_ratio: float = Field(ge=0.0, le=1.0)
    issue_count: int = 0
    unresolved_count: int = 0
    # rules.md §5 지표 중 이 phase에서 관찰된 항목
    observed_risk_categories: list[str] = Field(default_factory=list)
    # 0.0 ~ 1.0 (높을수록 이 phase 안정)
    phase_stability_score: float = Field(ge=0.0, le=1.0, default=1.0)


class PhaseLog(BaseModel):
    """단일 phase의 전체 실행 로그.

    하나의 phase 내 여러 scenario_event turn을 통합하여
    phase 단위 흐름, issue, 결정, action을 기록한다.
    """

    model_config = ConfigDict(extra="forbid")

    phase_name: str
    phase_objective: str
    trigger_sources: list[str] = Field(
        default_factory=list,
        description="이 phase에서 발동된 모든 trigger_source 합집합",
    )
    conversation_summary: str = Field(
        description="이 phase 전체 발언의 핵심 흐름 요약 (구조화 문장)"
    )
    participant_turns: list[ParticipantTurnSummary] = Field(default_factory=list)
    detected_issues: list[IssueCandidate] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    unresolved_questions: list[UnresolvedQuestion] = Field(default_factory=list)
    phase_scores: PhaseScore | None = None

    # raw_dialogue는 선택 저장 (기본 None)
    raw_dialogue: list[dict] | None = None


class TeamSimulationLog(BaseModel):
    """Team_Simulation_Log.json 전체 구조.

    Phase 8 Issue/Risk Evaluator의 1차 입력.
    """

    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    project_name: str
    team_id: str
    phase_logs: list[PhaseLog]
    total_issues: int = 0
    total_actions: int = 0
    total_unresolved: int = 0

    def model_post_init(self, __context) -> None:
        object.__setattr__(
            self, "total_issues", sum(len(p.detected_issues) for p in self.phase_logs)
        )
        object.__setattr__(self, "total_actions", sum(len(p.action_items) for p in self.phase_logs))
        object.__setattr__(
            self, "total_unresolved", sum(len(p.unresolved_questions) for p in self.phase_logs)
        )
