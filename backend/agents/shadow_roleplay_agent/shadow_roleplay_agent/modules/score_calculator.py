"""Phase 9 — Score Calculator

Issue_Risk_Summary + Team_Simulation_Log → Score_Breakdown.json

rules.md §5 가중치 공식:
  overall_project_fit =
    schedule_stability     * 0.20
  + role_clarity           * 0.15
  + technical_risk_control * 0.15
  + integration_readiness  * 0.15
  + collaboration_quality  * 0.15
  + qa_release_readiness   * 0.10
  + workload_balance       * 0.10

점수 산정 방식:
  각 차원은 1.0에서 시작해 연관 issue의 status × severity로 감점.
  CONFIRMED 우선 적용, CANDIDATE는 경감 적용.
  Team_Simulation_Log의 phase_stability_score도 해당 차원에 반영.

rules.md §6 Verdict Rule:
  not_recommended         if CONFIRMED HIGH release_blocker 또는 overall < 0.45
  needs_rebalancing       if CONFIRMED {role_conflict, unclear_ownership, workload_concentration}
                            또는 overall < 0.60
  proceed_with_conditions if must-fix CONFIRMED issue 존재
  proceed                 otherwise
"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.issue_risk_summary import (
    ConfirmedIssue,
    EvaluationStatus,
    IssueRiskSummary,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_log import (
    TeamSimulationLog,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.score_breakdown import (
    ScoreBreakdown,
    ScoreDimension,
    Verdict,
)

logger = logging.getLogger(__name__)

# ── 차원 메타데이터 ────────────────────────────────────────────────────

# (dimension_name, weight, related_categories)
_DIMENSIONS: list[tuple[str, float, list[str]]] = [
    ("schedule_stability", 0.20, ["schedule_risk"]),
    ("role_clarity", 0.15, ["role_conflict", "unclear_ownership"]),
    ("technical_risk_control", 0.15, ["technical_dependency_risk"]),
    ("integration_readiness", 0.15, ["integration_risk"]),
    ("collaboration_quality", 0.15, ["communication_delay"]),
    ("qa_release_readiness", 0.10, ["qa_coverage_gap", "release_blocker"]),
    ("workload_balance", 0.10, ["workload_concentration"]),
]

# issue status × severity 감점표
_PENALTY: dict[str, dict[str, float]] = {
    EvaluationStatus.CONFIRMED: {"high": 0.38, "medium": 0.26, "low": 0.14},
    EvaluationStatus.CANDIDATE: {"high": 0.20, "medium": 0.12, "low": 0.06},
}

# phase_name → 관련 차원 (phase_stability_score 반영)
_PHASE_DIMENSION_MAP: dict[str, list[str]] = {
    "Kickoff Meeting": ["schedule_stability", "role_clarity"],
    "Design Phase": ["role_clarity", "technical_risk_control"],
    "Development Phase": ["workload_balance", "technical_risk_control"],
    "Integration Phase": ["integration_readiness"],
    "QA / Release Phase": ["qa_release_readiness"],
}

# 차원별 phase stability 반영 가중치
_PHASE_STABILITY_WEIGHT = 0.15


class ScoreCalculator:
    """IssueRiskSummary + TeamSimulationLog → ScoreBreakdown.

    사용 방법:
        calc = ScoreCalculator()
        breakdown = calc.calculate(issue_summary, sim_log)
        ScoreCalculator.to_json(breakdown, path)
    """

    def calculate(
        self,
        issue_summary: IssueRiskSummary,
        sim_log: TeamSimulationLog,
    ) -> ScoreBreakdown:
        """7개 차원 점수와 overall_project_fit을 계산한다."""

        # ── 1. phase_stability 수집 ──────────────────────────────────
        phase_stability: dict[str, float] = {}
        for plog in sim_log.phase_logs:
            if plog.phase_scores:
                phase_stability[plog.phase_name] = plog.phase_scores.phase_stability_score

        # ── 2. 차원별 이슈 그룹핑 ────────────────────────────────────
        all_issues = issue_summary.confirmed_issues + issue_summary.candidate_issues

        # dimension → [ConfirmedIssue]
        dim_issues: dict[str, list[ConfirmedIssue]] = {d[0]: [] for d in _DIMENSIONS}
        for issue in all_issues:
            for dim_name, _, cats in _DIMENSIONS:
                if issue.issue_category in cats:
                    dim_issues[dim_name].append(issue)

        # ── 3. 차원별 점수 계산 ──────────────────────────────────────
        dimensions: list[ScoreDimension] = []
        overall = 0.0

        for dim_name, weight, _related_cats in _DIMENSIONS:
            raw_score, deducted_by, penalty_detail = _calc_dim_score(dim_name, dim_issues[dim_name])

            # phase_stability 조정
            phase_signal = ""
            rel_stabilities = [
                phase_stability.get(ph, 1.0)
                for ph, dims in _PHASE_DIMENSION_MAP.items()
                if dim_name in dims
            ]
            if rel_stabilities:
                avg_stability = sum(rel_stabilities) / len(rel_stabilities)
                adjusted = (
                    raw_score * (1 - _PHASE_STABILITY_WEIGHT)
                    + avg_stability * _PHASE_STABILITY_WEIGHT
                )
                phase_signal = f"phase_stability_avg={avg_stability:.3f} → score {raw_score:.3f}→{adjusted:.3f}"
                raw_score = round(min(1.0, max(0.0, adjusted)), 4)

            weighted = round(raw_score * weight, 4)
            overall += weighted

            dimensions.append(
                ScoreDimension(
                    dimension=dim_name,
                    weight=weight,
                    raw_score=raw_score,
                    weighted_score=weighted,
                    deducted_by=deducted_by,
                    penalty_detail=penalty_detail,
                    phase_signal=phase_signal,
                )
            )
            logger.info(
                "[ScoreCalc] %-25s raw=%.3f weight=%.2f weighted=%.3f",
                dim_name,
                raw_score,
                weight,
                weighted,
            )

        overall_fit = round(min(1.0, max(0.0, overall)), 4)

        # ── 4. Verdict 판정 (rules.md §6) ───────────────────────────
        verdict = _determine_verdict(issue_summary, dimensions, overall_fit)

        # ── 5. 진단 요약 생성 ────────────────────────────────────────
        top_risk = sorted(dimensions, key=lambda d: d.raw_score)[:3]
        top_risk_dims = [d.dimension for d in top_risk]

        must_fix = [
            i.issue_category for i in issue_summary.confirmed_issues if i.severity == "high"
        ]

        score_note = _build_score_note(sim_log.project_name, overall_fit, verdict, must_fix)

        breakdown = ScoreBreakdown(
            simulation_id=issue_summary.simulation_id,
            team_id=issue_summary.team_id,
            dimensions=dimensions,
            overall_project_fit=overall_fit,
            verdict=verdict,
            top_risk_dimensions=top_risk_dims,
            must_fix_categories=must_fix,
            score_note=score_note,
        )

        logger.info(
            "[ScoreCalculator] 완료 | overall=%.3f verdict=%s must_fix=%d",
            overall_fit,
            verdict,
            len(must_fix),
        )
        return breakdown

    @staticmethod
    def to_json(breakdown: ScoreBreakdown, path: Path | str) -> None:
        """Score_Breakdown.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(breakdown.model_dump_json(indent=2), encoding="utf-8")
        logger.info("[ScoreCalculator] 저장 완료 -> %s", out)


# ──────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────


def _calc_dim_score(
    dim_name: str,
    issues: list[ConfirmedIssue],
) -> tuple[float, list[str], list[str]]:
    """issue 목록에서 차원 raw_score(0~1)와 근거를 계산한다."""
    score = 1.0
    deducted_by: list[str] = []
    penalty_detail: list[str] = []

    for issue in issues:
        penalties = _PENALTY.get(issue.status, {})
        penalty = penalties.get(issue.severity, 0.0)
        if penalty:
            score -= penalty
            deducted_by.append(issue.issue_id)
            penalty_detail.append(
                f"{issue.issue_category}({issue.status}/{issue.severity}): -{penalty}"
            )

    raw = round(max(0.0, min(1.0, score)), 4)
    return raw, deducted_by, penalty_detail


def _determine_verdict(
    summary: IssueRiskSummary,
    dimensions: list[ScoreDimension],
    overall: float,
) -> Verdict:
    """rules.md §6 Verdict Rule을 적용한다."""
    confirmed_cats = {i.issue_category for i in summary.confirmed_issues}

    # not_recommended: release_blocker 확정 HIGH 또는 overall 매우 낮음
    release_blocker_confirmed = any(
        i.issue_category == "release_blocker" and i.severity == "high"
        for i in summary.confirmed_issues
    )
    if release_blocker_confirmed or overall < 0.45:
        return Verdict.NOT_RECOMMENDED

    # needs_rebalancing: 역할/소유권/workload 확정 이슈 또는 overall 낮음
    rebalance_cats = {"role_conflict", "unclear_ownership", "workload_concentration"}
    if confirmed_cats & rebalance_cats or overall < 0.60:
        return Verdict.NEEDS_REBALANCING

    # proceed_with_conditions: CONFIRMED issue 존재 (any severity)
    if summary.confirmed_issues:
        return Verdict.PROCEED_WITH_CONDITIONS

    # proceed: 모든 이슈 CANDIDATE 이하
    return Verdict.PROCEED


def _build_score_note(
    project_name: str,
    overall: float,
    verdict: Verdict,
    must_fix: list[str],
) -> str:
    """guardrails §6 권장 표현에 맞는 진단 요약 문장을 생성한다."""
    verdict_phrases = {
        Verdict.PROCEED: "이 팀 조합은 주어진 요구사항에 대해 안정적인 진행이 가능하다.",
        Verdict.PROCEED_WITH_CONDITIONS: "이 팀 조합은 진행 가능하나, 시작 전 해결이 필요한 항목이 존재한다.",
        Verdict.NEEDS_REBALANCING: "이 팀 조합은 역할·workload·ownership 재조정 후 진행을 권장한다.",
        Verdict.NOT_RECOMMENDED: "이 팀 조합은 현재 상태에서 프로젝트 착수를 권장하지 않는다.",
    }
    base = verdict_phrases.get(verdict, "")
    parts = [
        f"[{project_name}] simulation overall_project_fit = {overall:.3f}. {base}",
    ]
    if must_fix:
        parts.append(f"착수 전 필수 해결 카테고리: {', '.join(must_fix)}.")
    return " ".join(parts)
