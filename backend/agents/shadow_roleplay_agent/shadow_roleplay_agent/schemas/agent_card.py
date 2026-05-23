"""Phase 3 산출물 스키마 — Agent Card

guardrails.md §3 Agent 발언 규칙과 §2 허용 input을 기반으로
각 팀원 Agent의 프로파일을 정의한다.

설계 원칙 (Final_plan §0):
- Agent는 이름을 가진 팀원 자체의 시뮬레이션이다.
  역할·신호 데이터 범위 안에서 개인 성격과 감정 표현이 허용된다.
- agent_id는 직원 이름을 그대로 사용한다.
- 나이·성별·주소·학교 등 PII 및 원천 DB 원문은 포함하지 않는다.
"""

from pydantic import BaseModel, ConfigDict, Field

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    CollaborationStyle,
    DeliverySignal,
)

# guardrails §3 고정 발언 규칙 — 모든 Agent에 동일하게 적용
SPEAKING_RULES: list[str] = [
    "Speak only from your assigned role and responsibilities",
    "Do not invent private facts or personal attributes",
    "Raise concerns only when supported by evidence_refs",
    "Always return: observation, concern, dependency, proposed_action",
    "Do not simulate personal emotions or interpersonal conflicts",
]


class AgentCard(BaseModel):
    """시뮬레이션 역할 단위 Agent의 프로파일.

    Phase 6 Role Agent Execution에서 LLM 프롬프트 컨텍스트로 직접 사용된다.
    """

    model_config = ConfigDict(extra="forbid")

    # 직원 이름을 그대로 사용 (업무 식별 목적 / 개인정보 아님)
    agent_id: str = Field(description="직원 이름 (assigned role 식별자)")

    assigned_role: str

    # 이번 프로젝트에서 이 Agent가 담당하는 기능/작업 목록
    responsibilities: list[str] = Field(description="프로젝트 기능 중 이 역할이 소유하는 항목")

    # matched_skills 기반 — 이 역할이 잘할 수 있는 영역
    strengths: list[str] = Field(description="matched_skills에서 파생된 강점 항목")

    # missing_skills + signal 기반 — 이 역할의 제약 조건
    constraints: list[str] = Field(
        description="missing_skills, capacity/communication signal 기반 제약"
    )

    risk_tags: list[str] = Field(default_factory=list)

    # slack.collaboration_style 기반 협업 성향
    collaboration_signal: CollaborationStyle

    delivery_signal: DeliverySignal

    # 이 Agent의 발언·판단에 사용 가능한 원천 컬럼 참조 키
    evidence_refs: list[str] = Field(default_factory=list)

    # guardrails §3 고정 발언 규칙 (빌더가 자동 주입)
    speaking_rules: list[str] = Field(default_factory=list)
