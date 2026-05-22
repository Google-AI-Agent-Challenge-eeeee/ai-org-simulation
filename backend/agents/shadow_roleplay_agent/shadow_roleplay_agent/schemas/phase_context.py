"""Phase 6 컨텍스트 스키마 — Current Phase Context

Role Agent가 발언 시 '지금 어떤 상황인가'를 인식하는 최소 컨텍스트를 정의한다.

각 발언 전 Orchestrator가 이 컨텍스트를 Role Agent에 주입한다.
Agent는 이 컨텍스트 바깥의 사실을 생성해서는 안 된다 (guardrails §3).
"""

from pydantic import BaseModel, ConfigDict, Field

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_plan import (
    AgendaItem,
    PhaseName,
    ScenarioEvent,
)


class PeerRoleSummary(BaseModel):
    """같은 event에 참여하는 다른 역할의 간략 정보 (의존성 파악용)."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(default="", description="팀원 이름 (이름으로 호칭할 때 사용)")
    assigned_role: str
    risk_tags: list[str] = Field(default_factory=list)


class PhaseContext(BaseModel):
    """Role Agent 발언 직전에 주입되는 현재 phase 컨텍스트.

    Agent는 이 컨텍스트만을 사용해 발언을 구성해야 한다.
    여기에 없는 정보(원천 DB 값, 개인 정보, 타 phase 이벤트)는 언급 불가.
    """

    model_config = ConfigDict(extra="forbid")

    # 어떤 phase인지
    phase_name: PhaseName
    phase_objective: str

    # 이 발언을 유발한 event
    current_event: ScenarioEvent

    # 현재 phase의 agenda (Agent가 자신의 역할 범위를 확인하는 데 사용)
    phase_agenda: list[AgendaItem] = Field(default_factory=list)

    # 같은 event에 참여하는 다른 역할 요약 (의존성 표현에 사용)
    peer_roles: list[PeerRoleSummary] = Field(default_factory=list)

    # 이 Agent의 역할명 (발언 전 자기 역할 재확인용)
    speaking_agent_role: str

    # 이 Agent가 사용 가능한 evidence_refs (Agent Card에서 복사)
    available_evidence_refs: list[str] = Field(default_factory=list)
