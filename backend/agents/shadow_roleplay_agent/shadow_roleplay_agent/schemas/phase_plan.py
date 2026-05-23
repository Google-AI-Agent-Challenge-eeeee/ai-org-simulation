"""Phase 4 산출물 스키마 — Simulation Phase Plan

5개 고정 phase 각각의 agenda, scenario_event, trigger_source를 정의한다.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PhaseName(StrEnum):
    KICKOFF = "Kickoff Meeting"
    DESIGN = "Design Phase"
    DEVELOPMENT = "Development Phase"
    INTEGRATION = "Integration Phase"
    QA_RELEASE = "QA / Release Phase"


class AgendaItem(BaseModel):
    """phase 내 하나의 논의 항목."""

    model_config = ConfigDict(extra="forbid")

    topic: str
    owner_role: str
    related_features: list[str] = Field(default_factory=list)


class ScenarioEvent(BaseModel):
    """phase에서 발생시킬 시뮬레이션 이벤트.

    trigger_source는 risk_tag 또는 evidence_ref 참조 키이며
    Phase 6 Role Agent 발언 시 Orchestrator가 이 이벤트를 기반으로
    concern/dependency를 유도한다.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str
    description: str
    trigger_source: list[str] = Field(
        description="근거가 되는 risk_tag 또는 evidence_ref 참조 키 목록"
    )
    involved_roles: list[str] = Field(description="이 이벤트에 직접 관여되는 역할 목록")
    expected_issue_category: str = Field(description="rules.md §2 issue/risk 지표 중 해당 카테고리")


class SimulationPhase(BaseModel):
    """5개 고정 phase 중 하나의 실행 계획."""

    model_config = ConfigDict(extra="forbid")

    phase_name: PhaseName
    phase_objective: str
    agenda: list[AgendaItem]
    scenario_events: list[ScenarioEvent]
    focus_risk_tags: list[str] = Field(description="이 phase에서 집중 관찰할 risk_tag 목록")


class SimulationPhasePlan(BaseModel):
    """5개 phase 전체 실행 계획 묶음 — Phase 5 Orchestrator의 진행 기준."""

    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    project_name: str
    phases: list[SimulationPhase] = Field(min_length=5, max_length=5)
