"""Phase 5 — Simulation Orchestrator

Simulation_Phase_Plan + Agent_Cards를 기반으로:
1. phase 순서를 고정 (Kickoff → Design → Development → Integration → QA/Release)
2. 각 scenario_event마다 involved_roles 순서로 Role Agent 발언을 수집
3. 발언 형식(observation/concern/dependency/proposed_action) 준수 여부를 검증
4. 검증 실패 시 OrchestratorFlag(re_question / invalid_skip)를 부착
5. 모든 결과를 OrchestratorOutput으로 반환

guardrails §3 준수:
- 4개 필드 중 빈 항목 → INVALID, re_question 플래그
- concern에 evidence 근거 없음 → NEEDS_RETRY, re_question 플래그
- PII 키워드 → INVALID, invalid_skip 플래그
"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.phase_context_builder import (
    PhaseContextBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.role_agent import (
    RoleAgent,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.agent_card import (
    AgentCard,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.orchestrator import (
    AgentTurn,
    LLMMode,
    OrchestratorFlag,
    OrchestratorOutput,
    PhaseRun,
    ValidationStatus,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_plan import (
    ScenarioEvent,
    SimulationPhase,
    SimulationPhasePlan,
)

logger = logging.getLogger(__name__)

# Orchestrator가 role_agent에게 재질문하는 최대 횟수
_MAX_RETRY = 1


class SimulationOrchestrator:
    """Phase 5 — 시뮬레이션 진행 통제자.

    사용 방법:
        orch = SimulationOrchestrator(llm_mode=LLMMode.STUB)
        output = orch.run(plan, cards)
        SimulationOrchestrator.to_json(output, path)
    """

    def __init__(
        self,
        llm_mode: LLMMode = LLMMode.STUB,
        *,
        strict_llm: bool = False,
    ) -> None:
        self.llm_mode = llm_mode
        self.strict_llm = strict_llm

    def run(
        self,
        plan: SimulationPhasePlan,
        cards: list[AgentCard],
    ) -> OrchestratorOutput:
        """5개 phase 전체를 순서대로 실행하고 OrchestratorOutput을 반환한다."""
        card_by_role: dict[str, AgentCard] = {c.assigned_role: c for c in cards}
        ctx_builder = PhaseContextBuilder(cards)
        phase_runs: list[PhaseRun] = []

        for phase in plan.phases:
            logger.info(
                "[Orchestrator] phase=%s  events=%d",
                phase.phase_name.value,
                len(phase.scenario_events),
            )
            for event in phase.scenario_events:
                run = self._run_event(phase, event, card_by_role, ctx_builder)
                phase_runs.append(run)

        output = OrchestratorOutput(
            simulation_id=plan.simulation_id,
            llm_mode=self.llm_mode,
            phase_runs=phase_runs,
        )
        logger.info(
            "[Orchestrator] 완료 | total_turns=%d  total_invalid=%d",
            output.total_turns,
            output.total_invalid,
        )
        return output

    def run_stream(
        self,
        plan: SimulationPhasePlan,
        cards: list[AgentCard],
    ):
        """SSE 스트리밍용 Generator.

        turn이 완료될 때마다 즉시 yield해 FastAPI StreamingResponse로 전달한다.

        Yield 타입:
            {"type": "phase_start",  "phase": str, "phase_index": int, "objective": str}
            {"type": "event_start",  "event_id": str, "description": str, "trigger_source": list}
            {"type": "agent_turn",   "turn": dict, "agent_id": str, "role": str}
            {"type": "backend_log",  "text": str}
            {"type": "phase_end",    "phase": str}
            {"type": "done",         "total_turns": int}
        """
        card_by_role: dict[str, AgentCard] = {c.assigned_role: c for c in cards}
        ctx_builder = PhaseContextBuilder(cards)
        phase_runs: list[PhaseRun] = []
        total_turns = 0

        for phase_idx, phase in enumerate(plan.phases):
            yield {
                "type": "phase_start",
                "phase": phase.phase_name.value,
                "phase_index": phase_idx,
                "objective": phase.phase_objective,
            }
            yield {
                "type": "backend_log",
                "text": f"[Orchestrator] {phase.phase_name.value} — {len(phase.scenario_events)}개 이벤트 처리 시작",
            }

            for event in phase.scenario_events:
                yield {
                    "type": "event_start",
                    "event_id": event.event_id,
                    "description": event.description,
                    "trigger_source": event.trigger_source,
                }
                yield {
                    "type": "backend_log",
                    "text": f"[Orchestrator] {event.event_id} · {event.expected_issue_category} 처리 중",
                }

                run = self._run_event(phase, event, card_by_role, ctx_builder)
                phase_runs.append(run)
                total_turns += len(run.turns)

                for turn in run.turns:
                    yield {
                        "type": "agent_turn",
                        "agent_id": turn.agent_id,
                        "role": turn.assigned_role,
                        "validation": turn.validation.status if turn.validation else "valid",
                        "turn": {
                            "observation": turn.observation,
                            "concern": turn.concern,
                            "dependency": turn.dependency,
                            "proposed_action": turn.proposed_action,
                            "evidence_refs_used": turn.evidence_refs_used,
                        },
                    }
                    yield {
                        "type": "backend_log",
                        "text": f"[RoleAgent] {turn.agent_id}/{turn.assigned_role} → {turn.validation.status if turn.validation else 'valid'}",
                    }

                yield {"type": "event_end", "event_id": event.event_id}

            yield {"type": "phase_end", "phase": phase.phase_name.value}

        output = OrchestratorOutput(
            simulation_id=plan.simulation_id,
            llm_mode=self.llm_mode,
            phase_runs=phase_runs,
        )
        yield {"type": "done", "total_turns": total_turns, "output": output}

    def _run_event(
        self,
        phase: SimulationPhase,
        event: ScenarioEvent,
        card_by_role: dict[str, AgentCard],
        ctx_builder: PhaseContextBuilder,
    ) -> PhaseRun:
        """단일 scenario_event에 대한 turn 실행 — PhaseContext 주입."""
        turns: list[AgentTurn] = []
        flags: list[OrchestratorFlag] = []

        for role in event.involved_roles:
            card = card_by_role.get(role)
            if card is None:
                logger.warning("[Orchestrator] role=%s Agent Card 없음 (스킵)", role)
                flags.append(
                    OrchestratorFlag(
                        flag_type="invalid_skip",
                        agent_id=role,
                        event_id=event.event_id,
                        message=f"Agent Card 없음 — role={role}",
                    )
                )
                continue

            # Phase 6: PhaseContext 생성 후 speak_with_context 호출
            ctx = ctx_builder.build(phase, event, role)
            agent = RoleAgent(card, self.llm_mode, strict_llm=self.strict_llm)
            turn = agent.speak_with_context(ctx)

            # 검증 실패 시 재질문 (최대 1회)
            if turn.validation.status in (ValidationStatus.INVALID, ValidationStatus.NEEDS_RETRY):
                flag_type = (
                    "re_question"
                    if turn.validation.status == ValidationStatus.NEEDS_RETRY
                    else "invalid_skip"
                )
                flags.append(
                    OrchestratorFlag(
                        flag_type=flag_type,
                        agent_id=card.agent_id,
                        event_id=event.event_id,
                        message=(
                            f"[{turn.validation.status}] {turn.validation.reason} "
                            f"checks={turn.validation.failed_checks}"
                        ),
                    )
                )

                if flag_type == "re_question":
                    # NEEDS_RETRY: 재질문 1회 — PhaseContext 재주입
                    logger.info(
                        "[Orchestrator] re_question agent=%s event=%s",
                        card.agent_id,
                        event.event_id,
                    )
                    turn = agent.speak_with_context(ctx)

                if turn.validation.status == ValidationStatus.INVALID:
                    logger.warning(
                        "[Orchestrator] invalid_skip agent=%s event=%s reason=%s",
                        card.agent_id,
                        event.event_id,
                        turn.validation.reason,
                    )

            turns.append(turn)
            logger.debug(
                "[Orchestrator] turn added agent=%s status=%s",
                card.agent_id,
                turn.validation.status,
            )

        return PhaseRun(
            phase_name=phase.phase_name.value,
            event_id=event.event_id,
            event_desc=event.description,
            trigger_source=event.trigger_source,
            turns=turns,
            flags=flags,
        )

    @staticmethod
    def to_json(output: OrchestratorOutput, path: Path | str) -> None:
        """Orchestrator_Output.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            output.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("[Orchestrator] 저장 완료 -> %s", out)
