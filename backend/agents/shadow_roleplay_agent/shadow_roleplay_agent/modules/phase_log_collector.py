"""Phase 7 — Phase Log Collector

OrchestratorOutput을 받아 phase별 구조화 로그를 생성하고
Team_Simulation_Log.json으로 저장한다.

수집 항목:
  conversation_summary  : phase 내 발언 흐름 요약 문장 (구조화)
  participant_turns     : 유효 발언 요약 (raw_dialogue 아님)
  trigger_sources       : phase 내 모든 이벤트 trigger_source 합집합
  detected_issues       : concern + NEEDS_RETRY 발언에서 issue 후보 추출
  decisions             : VALID 발언의 proposed_action → 결정 사항으로 변환
  action_items          : dependency 있는 VALID 발언 → action 생성
  unresolved_questions  : NEEDS_RETRY / WARNING 발언 → 미해결 항목으로 기록
  phase_scores          : valid_turn_ratio, issue_count, stability_score 계산

raw_dialogue는 `save_raw=True` 옵션 시 저장 (기본 False).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.orchestrator import (
    OrchestratorOutput,
    PhaseRun,
    ValidationStatus,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_log import (
    ActionItem,
    Decision,
    IssueCandidate,
    IssueSeverity,
    IssueStatus,
    ParticipantTurnSummary,
    PhaseLog,
    PhaseScore,
    TeamSimulationLog,
    UnresolvedQuestion,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_plan import (
    SimulationPhasePlan,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    RequirementsList,
    SelectedTeamRecord,
)

logger = logging.getLogger(__name__)

# issue_category → severity 매핑 (rules.md §2 기준)
_SEVERITY_MAP: dict[str, IssueSeverity] = {
    "release_blocker":          IssueSeverity.HIGH,
    "integration_risk":         IssueSeverity.HIGH,
    "technical_dependency_risk":IssueSeverity.HIGH,
    "workload_concentration":   IssueSeverity.MEDIUM,
    "schedule_risk":            IssueSeverity.MEDIUM,
    "qa_coverage_gap":          IssueSeverity.MEDIUM,
    "communication_delay":      IssueSeverity.MEDIUM,
    "role_conflict":            IssueSeverity.HIGH,
    "unclear_ownership":        IssueSeverity.MEDIUM,
}


class PhaseLogCollector:
    """OrchestratorOutput + SimulationPhasePlan → TeamSimulationLog.

    사용 방법:
        collector = PhaseLogCollector()
        log = collector.collect(orch_output, plan, requirements, team)
        PhaseLogCollector.to_json(log, path)
    """

    def collect(
        self,
        orch_output: OrchestratorOutput,
        plan: SimulationPhasePlan,
        requirements: RequirementsList,
        team: SelectedTeamRecord,
        save_raw: bool = False,
    ) -> TeamSimulationLog:
        """Orchestrator 출력과 Phase Plan을 조합해 TeamSimulationLog를 생성한다."""

        # phase_name → [PhaseRun] 그룹핑
        runs_by_phase: dict[str, list[PhaseRun]] = {}
        for run in orch_output.phase_runs:
            runs_by_phase.setdefault(run.phase_name, []).append(run)

        # plan에서 phase_name → objective 매핑
        objective_by_phase: dict[str, str] = {
            p.phase_name.value: p.phase_objective for p in plan.phases
        }

        phase_logs: list[PhaseLog] = []
        issue_counter   = 1
        decision_counter = 1
        action_counter  = 1
        unresolved_counter = 1

        for phase_name, runs in runs_by_phase.items():
            # ── 각 항목 수집 ──────────────────────
            all_trigger_sources: set[str] = set()
            participant_turns:   list[ParticipantTurnSummary] = []
            detected_issues:     list[IssueCandidate] = []
            decisions:           list[Decision] = []
            action_items:        list[ActionItem] = []
            unresolved_questions:list[UnresolvedQuestion] = []
            raw_turns: list[dict] = []

            total_turns = 0
            valid_turns = 0

            for run in runs:
                all_trigger_sources.update(run.trigger_source)

                for turn in run.turns:
                    total_turns += 1

                    # participant_turns (구조화 요약)
                    participant_turns.append(ParticipantTurnSummary(
                        agent_id=turn.agent_id,
                        role=turn.assigned_role,
                        observation=turn.observation,
                        concern=turn.concern,
                        dependency=turn.dependency,
                        proposed_action=turn.proposed_action,
                        evidence_refs_used=turn.evidence_refs_used,
                        is_valid=(turn.validation.status == ValidationStatus.VALID),
                    ))

                    if save_raw:
                        raw_turns.append(turn.model_dump())

                    # VALID 발언 처리
                    if turn.validation.status == ValidationStatus.VALID:
                        valid_turns += 1

                        # concern → issue 후보
                        if turn.concern and "직접적 리스크" not in turn.concern and "모니터링" not in turn.concern:
                            issue_cat = _extract_issue_category(turn.concern, run.trigger_source)
                            detected_issues.append(IssueCandidate(
                                issue_id=f"issue_{issue_counter:03d}",
                                issue_category=issue_cat,
                                description=turn.concern,
                                raised_by=turn.agent_id,
                                raised_in_phase=phase_name,
                                trigger_source=run.trigger_source,
                                severity=_SEVERITY_MAP.get(issue_cat, IssueSeverity.LOW),
                                status=IssueStatus.CANDIDATE,
                                evidence_refs=turn.evidence_refs_used,
                            ))
                            issue_counter += 1

                        # proposed_action → decision
                        if turn.proposed_action and "완화 조치 가능" in turn.proposed_action:
                            decisions.append(Decision(
                                decision_id=f"dec_{decision_counter:03d}",
                                summary=turn.proposed_action[:120],
                                decided_by=turn.agent_id,
                                phase=phase_name,
                            ))
                            decision_counter += 1

                        # dependency → action_item
                        if (turn.dependency
                                and "단독 처리 가능" not in turn.dependency
                                and "의존 역할 없음" not in turn.dependency):
                            action_items.append(ActionItem(
                                action_id=f"act_{action_counter:03d}",
                                description=(
                                    f"{turn.dependency[:100]} "
                                    f"| 제안: {turn.proposed_action[:80]}"
                                ),
                                owner_role=turn.assigned_role,
                                phase=phase_name,
                                priority=_action_priority(turn.concern),
                                evidence_refs=turn.evidence_refs_used,
                            ))
                            action_counter += 1

                    # NEEDS_RETRY / WARNING → unresolved_question
                    elif turn.validation.status in (
                        ValidationStatus.NEEDS_RETRY, ValidationStatus.WARNING
                    ):
                        unresolved_questions.append(UnresolvedQuestion(
                            question_id=f"unres_{unresolved_counter:03d}",
                            description=(
                                f"[{turn.validation.status}] {turn.agent_id}({turn.assigned_role}) "
                                f"concern에 evidence 연결 미확보. "
                                f"concern: {turn.concern[:100]}"
                            ),
                            raised_by=turn.agent_id,
                            phase=phase_name,
                            risk_category=_extract_issue_category(
                                turn.concern, run.trigger_source
                            ),
                        ))
                        unresolved_counter += 1

            # ── Phase Score 계산 ─────────────────
            valid_ratio = valid_turns / total_turns if total_turns > 0 else 0.0
            issue_severity_penalty = sum(
                0.15 if i.severity == IssueSeverity.HIGH else
                0.08 if i.severity == IssueSeverity.MEDIUM else 0.03
                for i in detected_issues
            )
            stability = max(0.0, min(1.0, valid_ratio - issue_severity_penalty))

            phase_score = PhaseScore(
                phase=phase_name,
                valid_turn_ratio=round(valid_ratio, 3),
                issue_count=len(detected_issues),
                unresolved_count=len(unresolved_questions),
                observed_risk_categories=list({
                    i.issue_category for i in detected_issues
                }),
                phase_stability_score=round(stability, 3),
            )

            # ── conversation_summary 생성 ────────
            summary = _build_summary(phase_name, runs, detected_issues, unresolved_questions)

            phase_logs.append(PhaseLog(
                phase_name=phase_name,
                phase_objective=objective_by_phase.get(phase_name, ""),
                trigger_sources=sorted(all_trigger_sources),
                conversation_summary=summary,
                participant_turns=participant_turns,
                detected_issues=detected_issues,
                decisions=decisions,
                action_items=action_items,
                unresolved_questions=unresolved_questions,
                phase_scores=phase_score,
                raw_dialogue=raw_turns if save_raw else None,
            ))

            logger.info(
                "[PhaseLog] %s | turns=%d valid=%d issues=%d actions=%d unresolved=%d stability=%.2f",
                phase_name, total_turns, valid_turns,
                len(detected_issues), len(action_items),
                len(unresolved_questions), stability,
            )

        sim_log = TeamSimulationLog(
            simulation_id=orch_output.simulation_id,
            project_name=requirements.project_name,
            team_id=team.team_id,
            phase_logs=phase_logs,
        )
        logger.info(
            "[PhaseLogCollector] 완료 | phases=%d total_issues=%d total_actions=%d total_unresolved=%d",
            len(phase_logs), sim_log.total_issues, sim_log.total_actions, sim_log.total_unresolved,
        )
        return sim_log

    @staticmethod
    def to_json(log: TeamSimulationLog, path: Path | str) -> None:
        """Team_Simulation_Log.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            log.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("[PhaseLogCollector] 저장 완료 -> %s", out)


# ──────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────

def _extract_issue_category(concern_text: str, trigger_source: list[str]) -> str:
    """concern 텍스트 + trigger_source에서 rules.md issue category를 추출한다."""
    category_keywords: dict[str, list[str]] = {
        "workload_concentration":    ["workload", "과부하", "집중"],
        "schedule_risk":             ["schedule", "일정", "sprint", "완료율"],
        "integration_risk":          ["integration", "연동", "api", "블로킹"],
        "technical_dependency_risk": ["technical", "dependency", "sdk", "gcp", "cloud"],
        "qa_coverage_gap":           ["qa", "coverage", "e2e", "테스트", "playwright"],
        "communication_delay":       ["communication", "응답", "지연", "message"],
        "release_blocker":           ["release", "blocker", "릴리즈"],
        "role_conflict":             ["conflict", "충돌", "역할"],
        "unclear_ownership":         ["ownership", "owner", "공백"],
    }
    combined = (concern_text + " " + " ".join(trigger_source)).lower()
    for category, keywords in category_keywords.items():
        if any(kw in combined for kw in keywords):
            return category
    return "schedule_risk"


def _action_priority(concern_text: str) -> str:
    """concern 내용에서 action_item 우선순위를 추정한다."""
    high_keywords = ["high_risk", "블로킹", "release", "integration", "technical_dependency"]
    if any(kw in concern_text.lower() for kw in high_keywords):
        return "high"
    medium_keywords = ["medium_risk", "schedule", "workload", "qa"]
    if any(kw in concern_text.lower() for kw in medium_keywords):
        return "medium"
    return "low"


def _build_summary(
    phase_name: str,
    runs: list[PhaseRun],
    issues: list[IssueCandidate],
    unresolved: list[UnresolvedQuestion],
) -> str:
    """phase 내 발언 흐름을 구조화 요약 문장으로 생성한다."""
    event_ids = [r.event_id for r in runs]
    total_turns = sum(len(r.turns) for r in runs)
    issue_cats = list({i.issue_category for i in issues})
    high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]

    summary_parts = [
        f"{phase_name}: {len(event_ids)}개 이벤트({', '.join(event_ids)})에서 "
        f"{total_turns}건 발언이 수집됨.",
    ]
    if issue_cats:
        summary_parts.append(
            f"관찰된 issue 카테고리: {', '.join(issue_cats)}."
        )
    if high_issues:
        summary_parts.append(
            f"HIGH severity issue {len(high_issues)}건 — "
            f"{', '.join(i.issue_category for i in high_issues[:3])}."
        )
    if unresolved:
        summary_parts.append(
            f"evidence 미확보 발언 {len(unresolved)}건이 unresolved로 기록됨."
        )
    return " ".join(summary_parts)
