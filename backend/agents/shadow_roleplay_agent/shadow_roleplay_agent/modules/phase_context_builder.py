"""Phase 6 — Phase Context Builder

SimulationPhase + ScenarioEvent + AgentCards로부터
각 Role Agent에게 주입할 PhaseContext를 생성한다.

또한 모든 (phase, event, agent) 조합의 컨텍스트를
Current_Phase_Context.json으로 저장한다.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.agent_card import (
    AgentCard,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_context import (
    PeerRoleSummary,
    PhaseContext,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_plan import (
    ScenarioEvent,
    SimulationPhase,
    SimulationPhasePlan,
)

logger = logging.getLogger(__name__)


class PhaseContextBuilder:
    """(SimulationPhase, ScenarioEvent, AgentCard) → PhaseContext 생성기.

    사용 방법:
        builder = PhaseContextBuilder(cards)
        ctx = builder.build(phase, event, agent_role)
        # 또는 전체 저장
        all_ctxs = builder.build_all(plan)
        PhaseContextBuilder.to_json(all_ctxs, path)
    """

    def __init__(self, cards: list[AgentCard]) -> None:
        self._card_by_role: dict[str, AgentCard] = {c.assigned_role: c for c in cards}

    def build(
        self,
        phase: SimulationPhase,
        event: ScenarioEvent,
        agent_role: str,
    ) -> PhaseContext:
        """단일 (phase, event, agent_role) 조합의 PhaseContext를 반환한다."""
        card = self._card_by_role.get(agent_role)
        if card is None:
            raise ValueError(f"[ContextBuilder] AgentCard 없음: role={agent_role}")

        peer_roles = [
            PeerRoleSummary(
                agent_id=self._card_by_role[role].agent_id if role in self._card_by_role else role,
                assigned_role=role,
                risk_tags=self._card_by_role[role].risk_tags if role in self._card_by_role else [],
            )
            for role in event.involved_roles
            if role != agent_role
        ]

        return PhaseContext(
            phase_name=phase.phase_name,
            phase_objective=phase.phase_objective,
            current_event=event,
            phase_agenda=phase.agenda,
            peer_roles=peer_roles,
            speaking_agent_role=agent_role,
            available_evidence_refs=card.evidence_refs,
        )

    def build_all(self, plan: SimulationPhasePlan) -> list[dict]:
        """계획 전체 (모든 phase × event × role)의 PhaseContext 목록을 반환한다."""
        all_ctxs: list[dict] = []
        for phase in plan.phases:
            for event in phase.scenario_events:
                for role in event.involved_roles:
                    if role not in self._card_by_role:
                        logger.warning("[ContextBuilder] 카드 없음: role=%s (스킵)", role)
                        continue
                    ctx = self.build(phase, event, role)
                    all_ctxs.append(
                        {
                            "phase_name": ctx.phase_name.value,
                            "event_id": event.event_id,
                            "speaking_role": role,
                            "context": ctx.model_dump(),
                        }
                    )
        logger.info("[ContextBuilder] 총 %d개 PhaseContext 생성", len(all_ctxs))
        return all_ctxs

    @staticmethod
    def to_json(contexts: list[dict], path: Path | str) -> None:
        """Current_Phase_Context.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(contexts, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("[ContextBuilder] 저장 완료 -> %s", out)
