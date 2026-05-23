"""Phase 8 — Issue/Risk Evaluator

Team_Simulation_Log + Team_Risk_Summary + Evidence_Metadata를 교차 검증해
issue/risk를 CONFIRMED / CANDIDATE / INVALID으로 확정한다.

핵심 공식 (rules.md §3):
  final_issue_score = 0.4 * pre_simulation_risk
                    + 0.6 * observed_simulation_risk

확정 조건 (guardrails.md §5):
  Team_Risk_Summary 또는 Evidence_Metadata에 근거가 있고
  AND simulation log에서 concern/dependency/unresolved로 관찰됨

rules.md §4 분석 기준에 따라 카테고리별 root_cause, affected_roles,
suggested_action을 도출한다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.issue_risk_summary import (
    ConfirmedIssue,
    EvaluationStatus,
    IssueRiskSummary,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_log import (
    IssueCandidate,
    IssueSeverity,
    TeamSimulationLog,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    EvidenceMetadata,
    TeamRiskSummary,
)

logger = logging.getLogger(__name__)

# ── 상수 ───────────────────────────────────────────────────────────────

# rules.md §2 9개 공식 카테고리
_OFFICIAL_CATEGORIES = frozenset(
    {
        "role_conflict",
        "unclear_ownership",
        "schedule_risk",
        "workload_concentration",
        "technical_dependency_risk",
        "integration_risk",
        "communication_delay",
        "qa_coverage_gap",
        "release_blocker",
    }
)

# Team_Risk_Summary risk_tag → 공식 카테고리 매핑
_TAG_TO_CATEGORY: dict[str, str] = {
    "backend_workload_concentration": "workload_concentration",
    "pm_low_sprint_velocity": "schedule_risk",
    "fe_scope_instability": "schedule_risk",
    "fe_be_api_dependency": "integration_risk",
    "payment_api_integration_risk": "integration_risk",
    "devops_gcp_experience_gap": "technical_dependency_risk",
    "qa_communication_gap": "communication_delay",
    "qa_coverage_gap": "qa_coverage_gap",
    "schedule_risk": "schedule_risk",
    "integration_risk": "integration_risk",
}

# 공식 카테고리 → 분석 템플릿 (rules.md §4)
_CATEGORY_TEMPLATES: dict[str, dict] = {
    "role_conflict": {
        "root_cause": "동일 기능에 owner가 중복 선언되거나 Agent 간 책임 해석이 불일치함.",
        "suggested_action": "Kickoff 또는 Design phase에서 RACI 명확화 및 feature owner 단일화 진행.",
        "severity_default": "high",
    },
    "unclear_ownership": {
        "root_cause": "action item 또는 feature에 명확한 owner가 지정되지 않아 공백이 발생함.",
        "suggested_action": "모든 action_item에 owner_role을 명시하고 PM이 트래킹 보드에 반영.",
        "severity_default": "medium",
    },
    "schedule_risk": {
        "root_cause": "일정 제약, capacity 부족, 미해결 dependency가 복합적으로 관찰되어 마일스톤 달성 가능성이 낮아짐.",
        "suggested_action": "sprint_completion_rate 목표치(≥ 0.7) 미충족 시 scope cut 또는 인원 보강 검토.",
        "severity_default": "medium",
    },
    "workload_concentration": {
        "root_cause": "P0 기능과 과부하 이슈가 특정 역할(Backend Developer)에 집중. 미완료 Jira 이슈 누적.",
        "suggested_action": "작업 재분배 또는 buffer sprint 배정. 해당 역할의 P0/P1 우선순위 재조정.",
        "severity_default": "medium",
    },
    "technical_dependency_risk": {
        "root_cause": "미확보 기술(GCP Cloud Run, Payment SDK 등) 또는 외부 API에 대한 경험 부족으로 일정·품질 위험.",
        "suggested_action": "시작 전 기술 spike(PoC) 수행 또는 skill 보유자 추가 투입.",
        "severity_default": "high",
    },
    "integration_risk": {
        "root_cause": "API schema/DB/환경 의존성이 Integration phase까지 미확정으로 남아 교차 팀 블로킹 발생.",
        "suggested_action": "API schema를 Development phase 착수 전 Mock으로 우선 확정. 인터페이스 계약 문서화.",
        "severity_default": "high",
    },
    "communication_delay": {
        "root_cause": "동일 결정 사항이 여러 phase에서 반복 미해결. 응답 지연으로 의사결정 속도 저하.",
        "suggested_action": "QA-BE 간 정기 sync 일정 확보. Slack 응답 SLA(24h 이내) 팀 합의.",
        "severity_default": "medium",
    },
    "qa_coverage_gap": {
        "root_cause": "고위험 기능(결제, 인증)에 대한 e2e/예외 케이스 테스트가 누락. QA 착수 지연 확인.",
        "suggested_action": "Playwright e2e 시나리오 조기 작성. 결제·인증 플로우 happy/fail path 필수 커버.",
        "severity_default": "medium",
    },
    "release_blocker": {
        "root_cause": "QA/Release phase 종료 시점에 high severity unresolved issue가 미해소 상태로 존재.",
        "suggested_action": "릴리즈 전 must-fix 체크리스트 실행. 미해소 시 릴리즈 일정 연기 또는 feature flag 처리.",
        "severity_default": "high",
    },
}

# 확정(CONFIRMED) 임계값
_CONFIRM_THRESHOLD = 0.50


# ── 평가 내부 집계 구조 ────────────────────────────────────────────────


@dataclass
class _CategoryAccumulator:
    """카테고리별 수집 데이터."""

    candidates: list[IssueCandidate] = field(default_factory=list)
    phases_observed: set[str] = field(default_factory=set)
    all_evidence_refs: set[str] = field(default_factory=set)
    all_affected_roles: set[str] = field(default_factory=set)
    unresolved_ids: list[str] = field(default_factory=list)
    source_risk_tags: set[str] = field(default_factory=set)


class IssueRiskEvaluator:
    """Team_Simulation_Log + Team_Risk_Summary + EvidenceMetadata → IssueRiskSummary.

    사용 방법:
        evaluator = IssueRiskEvaluator()
        summary = evaluator.evaluate(sim_log, risk_summary, evidence_list)
        IssueRiskEvaluator.to_json(summary, path)
    """

    def evaluate(
        self,
        sim_log: TeamSimulationLog,
        risk_summary: TeamRiskSummary,
        evidence_list: list[EvidenceMetadata],
    ) -> IssueRiskSummary:
        """교차 검증 후 IssueRiskSummary를 반환한다."""

        # evidence_id 집합 — 근거 존재 여부 확인용
        evidence_ids: set[str] = {e.evidence_id for e in evidence_list}

        # ── 1. phase log에서 카테고리별 데이터 수집 ──────────────────
        accum: dict[str, _CategoryAccumulator] = {
            cat: _CategoryAccumulator() for cat in _OFFICIAL_CATEGORIES
        }

        for plog in sim_log.phase_logs:
            # IssueCandidate 수집
            for cand in plog.detected_issues:
                cat = _normalize_category(cand.issue_category)
                if cat not in accum:
                    continue
                a = accum[cat]
                a.candidates.append(cand)
                a.phases_observed.add(plog.phase_name)
                a.all_evidence_refs.update(cand.evidence_refs)
                a.source_risk_tags.update(cand.trigger_source)

            # unresolved_questions 수집
            for uq in plog.unresolved_questions:
                cat = _normalize_category(uq.risk_category)
                if cat not in accum:
                    continue
                accum[cat].unresolved_ids.append(uq.question_id)
                accum[cat].phases_observed.add(plog.phase_name)

            # participant_turns에서 dependency 보유 역할 수집
            for turn in plog.participant_turns:
                for cat in _OFFICIAL_CATEGORIES:
                    if cat in turn.dependency.lower() or cat in turn.concern.lower():
                        accum[cat].all_affected_roles.add(turn.role)

        # ── 2. Team_Risk_Summary pre_simulation_risk 매핑 ────────────
        # risk_tag → canonical category → pre_simulation_risk
        pre_scores: dict[str, float] = {}
        for tag, score in risk_summary.risk_prior_scores.items():
            cat = _TAG_TO_CATEGORY.get(tag, tag)
            if cat in _OFFICIAL_CATEGORIES:
                # 같은 category에 여러 tag가 있으면 최댓값
                pre_scores[cat] = max(pre_scores.get(cat, 0.0), score)

        # source_risk_tags를 pre_scores에도 반영
        for plog in sim_log.phase_logs:
            for cand in plog.detected_issues:
                for tag in cand.trigger_source:
                    cat = _TAG_TO_CATEGORY.get(tag, tag)
                    if cat in _OFFICIAL_CATEGORIES:
                        score = risk_summary.risk_prior_scores.get(tag, 0.0)
                        pre_scores[cat] = max(pre_scores.get(cat, 0.0), score)

        # ── 3. release_blocker 별도 감지 ─────────────────────────────
        # QA/Release phase에 unresolved high issue가 있으면 release_blocker 추가
        qa_unresolved_count = 0
        for plog in sim_log.phase_logs:
            if "QA" in plog.phase_name or "Release" in plog.phase_name:
                qa_unresolved_count += len(plog.unresolved_questions)
                high_issues = [i for i in plog.detected_issues if i.severity == IssueSeverity.HIGH]
                if high_issues or plog.unresolved_questions:
                    accum["release_blocker"].phases_observed.add(plog.phase_name)
                    for i in high_issues:
                        accum["release_blocker"].candidates.append(i)
                        accum["release_blocker"].all_evidence_refs.update(i.evidence_refs)
                    for uq in plog.unresolved_questions:
                        accum["release_blocker"].unresolved_ids.append(uq.question_id)

        # ── 4. 카테고리별 점수 계산 + 상태 판정 ──────────────────────
        confirmed: list[ConfirmedIssue] = []
        candidates: list[ConfirmedIssue] = []
        invalids: list[ConfirmedIssue] = []
        issue_counter = 1

        for cat in sorted(_OFFICIAL_CATEGORIES):
            a = accum[cat]
            tmpl = _CATEGORY_TEMPLATES[cat]

            # 근거(evidence) 확인
            has_prior_risk = cat in pre_scores and pre_scores[cat] > 0.0
            has_evidence = bool(a.all_evidence_refs & evidence_ids) or bool(
                a.source_risk_tags & set(risk_summary.risk_tags)
            )
            has_observation = len(a.candidates) > 0 or len(a.unresolved_ids) > 0

            if not has_observation and not has_prior_risk:
                # 관찰도 없고 prior risk도 없음 → INVALID
                invalids.append(
                    _make_issue(
                        issue_counter,
                        cat,
                        tmpl,
                        pre_simulation_risk=0.0,
                        observed_simulation_risk=0.0,
                        final_score=0.0,
                        status=EvaluationStatus.INVALID,
                        evidence_refs=[],
                        phases=[],
                        roles=[],
                        source_tags=[],
                        unresolved_ids=[],
                    )
                )
                issue_counter += 1
                continue

            # observed_simulation_risk 계산
            observed_risk = _calc_observed_risk(a, sim_log)

            pre_risk = pre_scores.get(cat, 0.0)
            final_score = round(0.4 * pre_risk + 0.6 * observed_risk, 4)

            # 확정 조건: guardrails §5
            guardrail_pass = (has_prior_risk or has_evidence) and has_observation

            if guardrail_pass and final_score >= _CONFIRM_THRESHOLD:
                status = EvaluationStatus.CONFIRMED
            elif has_observation:
                status = EvaluationStatus.CANDIDATE
            else:
                status = EvaluationStatus.INVALID

            affected = sorted(a.all_affected_roles) or _default_roles(cat)
            sev = _determine_severity(cat, final_score, a)
            root_cause = _enrich_root_cause(tmpl["root_cause"], cat, a)
            suggested = _enrich_suggested_action(tmpl["suggested_action"], a)

            issue = _make_issue(
                issue_counter,
                cat,
                tmpl,
                pre_simulation_risk=round(pre_risk, 4),
                observed_simulation_risk=round(observed_risk, 4),
                final_score=final_score,
                status=status,
                evidence_refs=sorted(a.all_evidence_refs),
                phases=sorted(a.phases_observed),
                roles=affected,
                source_tags=sorted(a.source_risk_tags),
                unresolved_ids=a.unresolved_ids,
                root_cause=root_cause,
                suggested_action=suggested,
                severity=sev,
            )
            issue_counter += 1

            if status == EvaluationStatus.CONFIRMED:
                confirmed.append(issue)
                logger.info(
                    "[Evaluator] CONFIRMED  %-30s score=%.3f phases=%s",
                    cat,
                    final_score,
                    sorted(a.phases_observed),
                )
            elif status == EvaluationStatus.CANDIDATE:
                candidates.append(issue)
                logger.info(
                    "[Evaluator] CANDIDATE  %-30s score=%.3f (below threshold or no prior)",
                    cat,
                    final_score,
                )
            else:
                invalids.append(issue)
                logger.debug("[Evaluator] INVALID    %s", cat)

        summary = IssueRiskSummary(
            simulation_id=sim_log.simulation_id,
            team_id=sim_log.team_id,
            confirmed_issues=confirmed,
            candidate_issues=candidates,
            invalid_issues=invalids,
        )
        logger.info(
            "[IssueRiskEvaluator] 완료 | confirmed=%d candidate=%d invalid=%d high=%d",
            summary.total_confirmed,
            summary.total_candidate,
            summary.total_invalid,
            summary.high_count,
        )
        return summary

    @staticmethod
    def to_json(summary: IssueRiskSummary, path: Path | str) -> None:
        """Issue_Risk_Summary.json으로 저장한다."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
        logger.info("[IssueRiskEvaluator] 저장 완료 -> %s", out)


# ──────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────


def _normalize_category(raw: str) -> str:
    """비공식 카테고리명을 공식 카테고리로 변환한다."""
    if raw in _OFFICIAL_CATEGORIES:
        return raw
    return _TAG_TO_CATEGORY.get(raw, raw)


def _calc_observed_risk(
    a: _CategoryAccumulator,
    sim_log: TeamSimulationLog,
) -> float:
    """simulation log 관찰치로 observed_simulation_risk(0~1)를 계산한다.

    severity별 가중치: HIGH=1.0, MEDIUM=0.6, LOW=0.3
    전체 phase 수로 정규화 후 0.95 cap.
    """
    total_phases = len(sim_log.phase_logs)
    if total_phases == 0:
        return 0.0

    weight_sum = 0.0
    for cand in a.candidates:
        if cand.severity == IssueSeverity.HIGH:
            weight_sum += 1.0
        elif cand.severity == IssueSeverity.MEDIUM:
            weight_sum += 0.6
        else:
            weight_sum += 0.3

    # unresolved 항목은 MEDIUM 가중치
    weight_sum += len(a.unresolved_ids) * 0.5

    # phase 수 대비 정규화
    raw = weight_sum / (total_phases * 1.5)
    return min(0.95, round(raw, 4))


def _determine_severity(cat: str, score: float, a: _CategoryAccumulator) -> str:
    """최종 점수와 후보 severity로 issue severity를 결정한다."""
    has_high = any(c.severity == IssueSeverity.HIGH for c in a.candidates)
    tmpl_default = _CATEGORY_TEMPLATES[cat]["severity_default"]

    if has_high or score >= 0.75:
        return "high"
    if score >= 0.50:
        return "medium" if tmpl_default != "high" else "high"
    return "low"


def _enrich_root_cause(base: str, cat: str, a: _CategoryAccumulator) -> str:
    """관찰 phase 목록을 근거로 root_cause를 보강한다."""
    if not a.phases_observed:
        return base
    phases_str = ", ".join(sorted(a.phases_observed))
    return f"{base} 관찰 phase: [{phases_str}]."


def _enrich_suggested_action(base: str, a: _CategoryAccumulator) -> str:
    """unresolved 수에 따라 긴급도 접두어를 추가한다."""
    if len(a.unresolved_ids) >= 2:
        return f"[긴급] {base}"
    return base


def _default_roles(cat: str) -> list[str]:
    """카테고리에 따른 기본 affected_roles."""
    _defaults: dict[str, list[str]] = {
        "role_conflict": ["PM", "Backend Developer", "Frontend Developer"],
        "unclear_ownership": ["PM"],
        "schedule_risk": ["PM", "Backend Developer"],
        "workload_concentration": ["Backend Developer"],
        "technical_dependency_risk": ["Backend Developer", "DevOps"],
        "integration_risk": ["Backend Developer", "Frontend Developer"],
        "communication_delay": ["QA Engineer", "Backend Developer"],
        "qa_coverage_gap": ["QA Engineer"],
        "release_blocker": ["PM", "QA Engineer"],
    }
    return _defaults.get(cat, ["PM"])


def _make_issue(
    counter: int,
    cat: str,
    tmpl: dict,
    *,
    pre_simulation_risk: float,
    observed_simulation_risk: float,
    final_score: float,
    status: EvaluationStatus,
    evidence_refs: list[str],
    phases: list[str],
    roles: list[str],
    source_tags: list[str],
    unresolved_ids: list[str],
    root_cause: str = "",
    suggested_action: str = "",
    severity: str = "",
) -> ConfirmedIssue:
    return ConfirmedIssue(
        issue_id=f"p8_issue_{counter:03d}",
        issue_category=cat,
        pre_simulation_risk=pre_simulation_risk,
        observed_simulation_risk=observed_simulation_risk,
        final_issue_score=final_score,
        severity=severity or tmpl["severity_default"],
        status=status,
        root_cause=root_cause or tmpl["root_cause"],
        affected_roles=roles or _default_roles(cat),
        suggested_action=suggested_action or tmpl["suggested_action"],
        evidence_refs=evidence_refs,
        observed_in_phases=phases,
        source_risk_tags=source_tags,
        unresolved_question_ids=unresolved_ids,
    )
