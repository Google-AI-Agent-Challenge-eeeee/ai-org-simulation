"""Phase 5/6 산출물 스키마 — Orchestrator & Role Agent Turn

Orchestrator가 통제하는 simulation 실행 결과를 정의한다.
각 AgentTurn은 Phase 7 Phase Log Collector의 입력이 된다.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class LLMMode(StrEnum):
    """LLM 연동 모드."""

    STUB = "stub"  # 규칙 기반 결정적 생성 (기본)
    VERTEX = "vertex"  # Vertex AI 연동 (추후)


class ValidationStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"  # 4개 필드 중 비어있는 항목 존재
    NEEDS_RETRY = "needs_retry"  # evidence 미확보 concern 존재
    WARNING = "warning"  # concern/dependency 있으나 약한 근거


class ValidationResult(BaseModel):
    """Orchestrator의 발언 검증 결과."""

    model_config = ConfigDict(extra="forbid")

    status: ValidationStatus
    failed_checks: list[str] = Field(default_factory=list)
    # INVALID/NEEDS_RETRY 사유 요약
    reason: str = ""


class AgentTurn(BaseModel):
    """Role Agent의 단일 발언 — guardrails §5 응답 형식 강제.

    4개 필드 모두 반드시 채워져야 한다.
    Orchestrator 검증 통과 여부가 is_valid에 기록된다.
    """

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    assigned_role: str

    # guardrails §5 고정 발언 포맷
    observation: str = Field(description="현재 phase에서 이 역할이 관찰한 사실")
    concern: str = Field(description="발생 가능한 위험 — evidence_ref 근거 필요")
    dependency: str = Field(description="다른 역할/기능/API에 대한 의존성")
    proposed_action: str = Field(description="완화 또는 해결 제안")

    # 이 발언에서 실제 참조된 evidence_refs
    evidence_refs_used: list[str] = Field(default_factory=list)

    # Orchestrator 검증 결과
    validation: ValidationResult

    # stub 모드 여부
    llm_mode: LLMMode = LLMMode.STUB


class OrchestratorFlag(BaseModel):
    """Orchestrator가 발언에 부착하는 플래그 (재질문, 경고, 스킵)."""

    model_config = ConfigDict(extra="forbid")

    flag_type: str  # "re_question" | "invalid_skip" | "warning"
    agent_id: str
    event_id: str
    message: str


class PhaseRun(BaseModel):
    """하나의 scenario_event에 대한 전체 turn 실행 결과."""

    model_config = ConfigDict(extra="forbid")

    phase_name: str
    event_id: str
    event_desc: str
    trigger_source: list[str]
    turns: list[AgentTurn]
    flags: list[OrchestratorFlag] = Field(default_factory=list)

    @property
    def valid_turns(self) -> list[AgentTurn]:
        return [t for t in self.turns if t.validation.status == ValidationStatus.VALID]

    @property
    def invalid_count(self) -> int:
        return sum(1 for t in self.turns if t.validation.status == ValidationStatus.INVALID)


class OrchestratorOutput(BaseModel):
    """Phase 5/6 전체 실행 결과 — Phase 7 Phase Log Collector의 입력."""

    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    llm_mode: LLMMode
    phase_runs: list[PhaseRun]
    total_turns: int = 0
    total_invalid: int = 0

    def model_post_init(self, __context) -> None:
        object.__setattr__(self, "total_turns", sum(len(r.turns) for r in self.phase_runs))
        object.__setattr__(self, "total_invalid", sum(r.invalid_count for r in self.phase_runs))
