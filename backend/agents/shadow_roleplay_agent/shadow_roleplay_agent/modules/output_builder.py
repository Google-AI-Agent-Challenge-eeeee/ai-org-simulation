"""Phase 10 — Output Builder

Score_Breakdown + Issue_Risk_Summary + Team_Simulation_Log
→ Simulation_OUTPUT.json (최종 통합 산출물)

추천/보정 로직 없음.
simulation_verdict와 must_fix_before_start는 Score_Breakdown에서 직접 인용하며
guardrails §6 권장 표현을 준수한다.
"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.issue_risk_summary import (
    EvaluationStatus,
    IssueRiskSummary,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_log import (
    IssueSeverity,
    TeamSimulationLog,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.score_breakdown import (
    ScoreBreakdown,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_output import (
    DimensionSummary,
    EvidenceSummary,
    MustFixItem,
    SimulationOutput,
    TopRisk,
)

logger = logging.getLogger(__name__)

# raw_score → status 매핑
def _dim_status(score: float) -> str:
    if score >= 0.75:
        return "good"
    if score >= 0.55:
        return "warning"
    return "critical"


class OutputBuilder:
    """Phase 10: 최종 Simulation_OUTPUT.json 조립.

    사용 방법:
        builder = OutputBuilder()
        output = builder.build(breakdown, issue_summary, sim_log, project_name)
        OutputBuilder.to_json(output, path)
    """

    def build(
        self,
        breakdown:     ScoreBreakdown,
        issue_summary: IssueRiskSummary,
        sim_log:       TeamSimulationLog,
        project_name:  str,
    ) -> SimulationOutput:
        """3개 중간 산출물을 조합해 SimulationOutput을 반환한다."""

        # ── 1. 차원별 점수 요약 ───────────────────────────────────────
        score_breakdown = [
            DimensionSummary(
                dimension=d.dimension,
                raw_score=d.raw_score,
                weighted_score=d.weighted_score,
                weight=d.weight,
                status=_dim_status(d.raw_score),
            )
            for d in breakdown.dimensions
        ]

        # ── 2. top_risks — CONFIRMED 우선, 이후 CANDIDATE HIGH ────────
        all_issues = list(issue_summary.confirmed_issues) + [
            i for i in issue_summary.candidate_issues if i.severity == "high"
        ]
        # final_issue_score 내림차순 정렬
        all_issues.sort(key=lambda i: i.final_issue_score, reverse=True)

        top_risks: list[TopRisk] = []
        for rank, issue in enumerate(all_issues[:5], start=1):
            top_risks.append(TopRisk(
                rank=rank,
                issue_category=issue.issue_category,
                severity=issue.severity,
                status=issue.status.value,
                observed_in_phases=issue.observed_in_phases,
                suggested_action=issue.suggested_action,
                evidence_refs=issue.evidence_refs[:5],
            ))

        # ── 3. must_fix_before_start — CONFIRMED issues ───────────────
        must_fix: list[MustFixItem] = [
            MustFixItem(
                issue_category=i.issue_category,
                severity=i.severity,
                suggested_action=i.suggested_action,
                affected_roles=i.affected_roles,
            )
            for i in issue_summary.confirmed_issues
        ]

        # ── 4. evidence_summary ───────────────────────────────────────
        all_evidence_refs: set[str] = set()
        for plog in sim_log.phase_logs:
            for turn in plog.participant_turns:
                all_evidence_refs.update(turn.evidence_refs_used)

        high_risk_phases = [
            plog.phase_name
            for plog in sim_log.phase_logs
            if plog.phase_scores and plog.phase_scores.phase_stability_score < 0.55
        ]

        evidence_summary = EvidenceSummary(
            total_evidence_refs=len(all_evidence_refs),
            total_confirmed_issues=issue_summary.total_confirmed,
            total_candidate_issues=issue_summary.total_candidate,
            total_unresolved_turns=sim_log.total_unresolved,
            phases_with_high_risk=high_risk_phases,
        )

        # ── 5. phase_stability_summary ────────────────────────────────
        phase_stability: dict[str, float] = {}
        for plog in sim_log.phase_logs:
            if plog.phase_scores:
                phase_stability[plog.phase_name] = plog.phase_scores.phase_stability_score

        # ── 6. SimulationOutput 조립 ──────────────────────────────────
        output = SimulationOutput(
            simulation_id=breakdown.simulation_id,
            team_id=breakdown.team_id,
            project_name=project_name,
            simulation_verdict=breakdown.verdict,
            overall_project_fit=breakdown.overall_project_fit,
            score_note=breakdown.score_note,
            score_breakdown=score_breakdown,
            top_risks=top_risks,
            must_fix_before_start=must_fix,
            evidence_summary=evidence_summary,
            phase_stability_summary=phase_stability,
        )

        logger.info(
            "[OutputBuilder] 완료 | verdict=%s overall=%.3f top_risks=%d must_fix=%d",
            output.simulation_verdict,
            output.overall_project_fit,
            len(output.top_risks),
            len(output.must_fix_before_start),
        )
        return output

    @staticmethod
    def to_json(output: SimulationOutput, path: "Path | str") -> None:
        """Simulation_OUTPUT.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output.model_dump_json(indent=2), encoding="utf-8")
        logger.info("[OutputBuilder] 저장 완료 -> %s", out)
