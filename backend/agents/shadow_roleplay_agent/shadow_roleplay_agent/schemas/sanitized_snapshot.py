"""Phase 2 산출물 스키마 — Sanitized Profile Snapshot

Privacy_and_Column_Filter 통과 후 남는 필드만 정의한다.

허용 필드 근거: shadow_roleplay_agent_guardrails.md §2 허용 input 목록
  employee_name, assigned_role, matched_skills, missing_skills,
  capacity_signal, communication_signal, delivery_signal,
  collaboration_signal, risk_tags, evidence_refs

제거 필드:
  employee_id          — 원천 HR DB PK (시스템 식별자)
  cross-system IDs     — github_id, slack_user_id, jira_account_id 등
  personal attributes  — 나이, 성별, 주소, 학교, 개인 프로필

최종 output(보고서)에서는 employee_name도 제거해야 하지만,
Phase 3 Agent Card 생성 단계까지는 이름을 유지한다.
"""

from pydantic import BaseModel, ConfigDict, Field

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    CapacitySignal,
    CollaborationStyle,
    CommunicationSignal,
    DeliverySignal,
)


class SanitizedProfileSnapshot(BaseModel):
    """guardrails §2 허용 목록만 포함한 팀원 스냅샷.

    Phase 3 Agent Card Builder와 Phase 6 Role Agent Execution의 유일한 직원 정보 소스다.
    """

    model_config = ConfigDict(extra="forbid")

    # 허용: 이름은 Phase 3 Agent Card 생성까지 유지
    employee_name: str

    assigned_role: str
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)

    capacity_signal: CapacitySignal
    communication_signal: CommunicationSignal
    delivery_signal: DeliverySignal
    collaboration_signal: CollaborationStyle

    risk_tags: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class FilterAuditLog(BaseModel):
    """필터가 제거한 필드를 추적하는 감사 로그."""

    model_config = ConfigDict(extra="forbid")

    employee_name: str
    removed_fields: list[str]
    retained_fields: list[str]
