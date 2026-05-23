"""Phase 3 — Agent Card Builder

Sanitized_Profile_Snapshot + RequirementsList를 조합해
각 팀원에 대한 역할 단위 AgentCard를 생성한다.

생성 로직:
  responsibilities = 프로젝트 기능(Feature) 중 assigned_role 해당 항목
                   + matched_skills (역할 수행 능력 근거)
  strengths        = matched_skills → 강점 문장으로 변환
  constraints      = missing_skills + capacity/communication signal 경고 문장
  speaking_rules   = guardrails §3 고정 규칙 (SPEAKING_RULES 상수)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.agent_card import (
    SPEAKING_RULES,
    AgentCard,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.sanitized_snapshot import (
    SanitizedProfileSnapshot,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    CapacitySignal,
    CommunicationSignal,
    RequirementsList,
)

logger = logging.getLogger(__name__)


class AgentCardBuilder:
    """SanitizedProfileSnapshot 목록을 AgentCard 목록으로 변환한다.

    사용 방법:
        builder = AgentCardBuilder()
        cards = builder.build(snapshots, requirements)
        AgentCardBuilder.to_json(cards, path)
    """

    def build(
        self,
        snapshots: list[SanitizedProfileSnapshot],
        requirements: RequirementsList,
    ) -> list[AgentCard]:
        """각 snapshot마다 AgentCard를 생성하고 리스트로 반환한다."""
        cards: list[AgentCard] = []
        for snap in snapshots:
            card = self._build_one(snap, requirements)
            cards.append(card)
            logger.info(
                "[AgentCardBuilder] %s (%s) | responsibilities=%d strengths=%d constraints=%d",
                card.agent_id,
                card.assigned_role,
                len(card.responsibilities),
                len(card.strengths),
                len(card.constraints),
            )
        logger.info("[AgentCardBuilder] 완료 | %d개 Agent Card 생성", len(cards))
        return cards

    @staticmethod
    def _build_one(
        snap: SanitizedProfileSnapshot,
        req: RequirementsList,
    ) -> AgentCard:
        """단일 snapshot → AgentCard 변환."""

        responsibilities = _derive_responsibilities(snap, req)
        strengths = _derive_strengths(snap)
        constraints = _derive_constraints(snap)

        return AgentCard(
            agent_id=snap.employee_name,
            assigned_role=snap.assigned_role,
            responsibilities=responsibilities,
            strengths=strengths,
            constraints=constraints,
            risk_tags=snap.risk_tags,
            collaboration_signal=snap.collaboration_signal,
            delivery_signal=snap.delivery_signal,
            evidence_refs=snap.evidence_refs,
            speaking_rules=list(SPEAKING_RULES),
        )

    @staticmethod
    def to_json(cards: list[AgentCard], path: Path | str) -> None:
        """Agent_Cards.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        data = [c.model_dump() for c in cards]
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[AgentCardBuilder] 저장 완료 -> %s", out)


# ──────────────────────────────────────────────
# 파생 로직 (private helpers)
# ──────────────────────────────────────────────


def _derive_responsibilities(
    snap: SanitizedProfileSnapshot,
    req: RequirementsList,
) -> list[str]:
    """이 역할이 담당하는 프로젝트 기능 + matched_skills 기반 항목을 조합한다."""
    items: list[str] = []

    # 1) RequirementsList.features 중 assigned_role 일치 항목
    for feat in req.features:
        if feat.assigned_role == snap.assigned_role:
            items.append(f"{feat.feature_name} ({feat.priority.value})")

    # 2) 기능이 없는 역할(PM 등)은 matched_skills로 보완
    if not items:
        items = [f"[역량] {s}" for s in snap.matched_skills]

    return items


def _derive_strengths(snap: SanitizedProfileSnapshot) -> list[str]:
    """matched_skills를 강점 문장으로 변환한다."""
    return [f"{skill} 경험 보유" for skill in snap.matched_skills]


def _derive_constraints(snap: SanitizedProfileSnapshot) -> list[str]:
    """missing_skills와 signal 수준에서 제약 문장을 생성한다."""
    items: list[str] = []

    # 1) missing_skills → 기술 제약
    for skill in snap.missing_skills:
        items.append(f"스킬 부재: {skill}")

    # 2) capacity_signal 경고
    if snap.capacity_signal == CapacitySignal.HIGH_RISK:
        items.append("capacity_signal=high_risk: 업무 과부하 우려, 추가 task 수용 제한")
    elif snap.capacity_signal == CapacitySignal.MEDIUM_RISK:
        items.append("capacity_signal=medium_risk: 여유 capacity 제한적")

    # 3) communication_signal 경고
    if snap.communication_signal == CommunicationSignal.HIGH_DELAY:
        items.append(
            "communication_signal=high_delay: 슬랙 응답 지연 (90분+), 의사결정 블로킹 우려"
        )
    elif snap.communication_signal == CommunicationSignal.MEDIUM_DELAY:
        items.append("communication_signal=medium_delay: 응답 시간 30~90분 수준")

    return items
