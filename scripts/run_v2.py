"""samples_v2 전체 파이프라인 실행 스크립트

프로젝트: AI 고객 서비스 챗봇 플랫폼 v1.0
팀:       이지훈(PM) / 최민준(BE) / 김서연(FE) / 박준혁(QA) / 오하은(ML Engineer)

samples/과 다른 리스크 프로파일:
  - be_ml_integration_risk (ML-BE 인터페이스 미확정)
  - ml_model_latency_risk (LLM 응답 지연)
  - qa_ai_coverage_gap (AI 응답 품질 검증 공백)
  - scope_creep_risk (PM 범위 확장 패턴)
  - ml_workload_concentration (ML Engineer 단독 집중)

실행:
  cd c:\\workspace\\ai-org-simulation
  $env:PYTHONUTF8 = "1"
  uv run python scripts/run_v2.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── v2 신규 risk_tag 런타임 확장 ─────────────────────────────

# 1. IssueRiskEvaluator: TAG → 공식 카테고리 매핑
import backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.issue_risk_evaluator as _ev_mod

_ev_mod._TAG_TO_CATEGORY.update(
    {
        "be_ml_integration_risk": "integration_risk",
        "ml_model_latency_risk": "technical_dependency_risk",
        "qa_ai_coverage_gap": "qa_coverage_gap",
        "fe_streaming_inexperience": "technical_dependency_risk",
        "ml_workload_concentration": "workload_concentration",
        "scope_creep_risk": "schedule_risk",
    }
)

# 2. ScenarioPhasePlanner: focus_categories + event templates 확장
import backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.scenario_phase_planner as _pl_mod
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.phase_plan import PhaseName

# Phase별 focus_categories에 v2 태그 추가
_pl_mod._PHASE_DEFINITIONS[PhaseName.KICKOFF]["focus_categories"].update(
    {
        "scope_creep_risk",
        "ml_workload_concentration",
    }
)
_pl_mod._PHASE_DEFINITIONS[PhaseName.DESIGN]["focus_categories"].update(
    {
        "be_ml_integration_risk",
        "ml_model_latency_risk",
        "fe_streaming_inexperience",
    }
)
_pl_mod._PHASE_DEFINITIONS[PhaseName.DEVELOPMENT]["focus_categories"].update(
    {
        "ml_workload_concentration",
        "scope_creep_risk",
        "be_ml_integration_risk",
    }
)
_pl_mod._PHASE_DEFINITIONS[PhaseName.INTEGRATION]["focus_categories"].update(
    {
        "be_ml_integration_risk",
        "fe_streaming_inexperience",
    }
)
_pl_mod._PHASE_DEFINITIONS[PhaseName.QA_RELEASE]["focus_categories"].update(
    {
        "qa_ai_coverage_gap",
        "qa_communication_gap",
    }
)

# v2 risk_tag → scenario event 템플릿 추가
_pl_mod._RISK_EVENT_TEMPLATES.update(
    {
        "be_ml_integration_risk": {
            "description": "ML 엔진 응답 스키마가 미확정 상태로 BE API 설계가 지연되고 있음. ML-BE 인터페이스 계약 미확정 시 FE 스트리밍 연동까지 도미노 블로킹 위험.",
            "involved_roles": ["ML Engineer", "Backend Developer", "Frontend Developer"],
            "expected_issue_category": "integration_risk",
        },
        "ml_model_latency_risk": {
            "description": "LLM 응답 지연 및 프롬프트 반복 개선으로 ML 미완료 이슈 5건 누적. 오하은(ML) 워크로드 초과 및 응답 품질 편차가 전체 일정에 영향 가능.",
            "involved_roles": ["ML Engineer", "PM"],
            "expected_issue_category": "technical_dependency_risk",
        },
        "qa_ai_coverage_gap": {
            "description": "AI 응답 비결정성으로 기존 E2E 자동화 기준 적용 불가. 박준혁(QA)의 AI 품질 평가 경험 부재로 결제/분류 오류 케이스 누락 시 릴리즈 blocker 가능.",
            "involved_roles": ["QA Engineer", "ML Engineer", "PM"],
            "expected_issue_category": "qa_coverage_gap",
        },
        "scope_creep_risk": {
            "description": "이지훈(PM)의 scope change 8회 패턴 확인. AI 기능 가능성 과대 평가로 인한 요구사항 추가 반복이 오하은(ML) 과부하로 직결될 위험.",
            "involved_roles": ["PM", "ML Engineer"],
            "expected_issue_category": "schedule_risk",
        },
        "ml_workload_concentration": {
            "description": "오하은(ML)의 워크로드(162.5시간)가 팀 평균 대비 37% 초과. ML 엔진 단독 담당 구조에서 추가 scope 흡수 여력 없음.",
            "involved_roles": ["ML Engineer", "PM", "Backend Developer"],
            "expected_issue_category": "workload_concentration",
        },
        "fe_streaming_inexperience": {
            "description": "김서연(FE)의 WebSocket/SSE 스트리밍 구현 경험 부재. 재오픈 이슈 4건 패턴으로 초기 구현 후 수정 반복 예상. BE WebSocket API 완료 후 연동 착수 지연 가능.",
            "involved_roles": ["Frontend Developer", "Backend Developer"],
            "expected_issue_category": "technical_dependency_risk",
        },
    }
)

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules import (
    AgentCardBuilder,
    IssueRiskEvaluator,
    OutputBuilder,
    PhaseLogCollector,
    PrivacyColumnFilter,
    ScenarioPhasePlanner,
    ScoreCalculator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline import (
    SimulationInputBuilder,
    SimulationOrchestrator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    EvidenceMetadata,
    RequirementsList,
    SelectedTeamRecord,
    TeamRiskSummary,
)

SAMPLES = ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/samples_v2"
OUTPUTS = ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs_v2"
OUTPUTS.mkdir(exist_ok=True)

print("=" * 60)
print("  AI 고객 서비스 챗봇 플랫폼 v1.0 — Shadow RolePlay 시뮬레이션")
print("=" * 60)

# ── Phase 1: SimulationInputBuilder ───────────────────────────
print("\n[Phase 1] SimulationInputBuilder")
builder = SimulationInputBuilder()
packet, evidence_index = builder.build(
    requirements=SAMPLES / "sample_requirements_list_v2.json",
    team_record=SAMPLES / "sample_selected_team_record_v2.json",
    snapshots=SAMPLES / "sample_employee_fit_profile_snapshots_v2.json",
    risk_summary=SAMPLES / "sample_team_risk_summary_v2.json",
    evidence_metadata=SAMPLES / "sample_evidence_metadata_v2.json",
)
print(f"  project  : {packet.project_context.project_name}")
print(f"  team     : {packet.selected_team.team_id}  ({len(packet.member_snapshots)}명)")
print(f"  evidence : {len(packet.evidence_metadata)}건")

requirements_full = RequirementsList.model_validate(
    json.loads((SAMPLES / "sample_requirements_list_v2.json").read_text(encoding="utf-8"))
)
team = SelectedTeamRecord.model_validate(
    json.loads((SAMPLES / "sample_selected_team_record_v2.json").read_text(encoding="utf-8"))
)
risk_summary = TeamRiskSummary.model_validate(
    json.loads((SAMPLES / "sample_team_risk_summary_v2.json").read_text(encoding="utf-8"))
)
evidence_list = [
    EvidenceMetadata.model_validate(e)
    for e in json.loads((SAMPLES / "sample_evidence_metadata_v2.json").read_text(encoding="utf-8"))
]

# ── Phase 2: PrivacyColumnFilter ──────────────────────────────
print("\n[Phase 2] PrivacyColumnFilter")
result = PrivacyColumnFilter().filter(packet)
print(f"  sanitized snapshots : {len(result.sanitized_snapshots)}명")

# ── Phase 3: AgentCardBuilder ─────────────────────────────────
print("\n[Phase 3] AgentCardBuilder")
cards = AgentCardBuilder().build(result.sanitized_snapshots, requirements_full)
print(f"  agent cards : {len(cards)}장")
for c in cards:
    print(f"    [{c.assigned_role}] {c.agent_id}  risks={c.risk_tags}")

# ── Phase 4: ScenarioPhasePlanner ─────────────────────────────
print("\n[Phase 4] ScenarioPhasePlanner")
plan = ScenarioPhasePlanner().plan(
    requirements_full, risk_summary, evidence_index, simulation_id="sim_v2_chatbot"
)
for p in plan.phases:
    print(f"  {p.phase_name.value:<22}  events={len(p.scenario_events)}")

# ── Phase 5/6: Orchestrator + RoleAgent ───────────────────────
print("\n[Phase 5/6] SimulationOrchestrator + RoleAgent")
orch_out = SimulationOrchestrator(llm_mode="stub").run(plan, cards)
total_turns = sum(len(r.turns) for r in orch_out.phase_runs)
invalid_turns = sum(
    1 for r in orch_out.phase_runs for t in r.turns if t.validation.status != "valid"
)
print(f"  phase_runs  : {len(orch_out.phase_runs)}")
print(f"  total turns : {total_turns}")
print(f"  non-valid   : {invalid_turns}")

# ── Phase 7: PhaseLogCollector ────────────────────────────────
print("\n[Phase 7] PhaseLogCollector")
sim_log = PhaseLogCollector().collect(orch_out, plan, requirements_full, team)
print(f"  phases      : {len(sim_log.phase_logs)}")
print(f"  total issues: {sim_log.total_issues}")
print(f"  actions     : {sim_log.total_actions}")
print(f"  unresolved  : {sim_log.total_unresolved}")
PhaseLogCollector.to_json(sim_log, OUTPUTS / "Team_Simulation_Log_v2.json")

# ── Phase 8: IssueRiskEvaluator ───────────────────────────────
print("\n[Phase 8] IssueRiskEvaluator")
issue_summary = IssueRiskEvaluator().evaluate(sim_log, risk_summary, evidence_list)
print(f"  confirmed : {issue_summary.total_confirmed}")
print(f"  candidate : {issue_summary.total_candidate}")
print(f"  invalid   : {issue_summary.total_invalid}")
print(
    f"  HIGH/MED/LOW : {issue_summary.high_count}/{issue_summary.medium_count}/{issue_summary.low_count}"
)
IssueRiskEvaluator.to_json(issue_summary, OUTPUTS / "Issue_Risk_Summary_v2.json")

# ── Phase 9: ScoreCalculator ──────────────────────────────────
print("\n[Phase 9] ScoreCalculator")
breakdown = ScoreCalculator().calculate(issue_summary, sim_log)
bar_w = 25
print(f"  {'Dimension':<25} {'Raw':>5}  Score bar")
for d in breakdown.dimensions:
    bar = "#" * int(d.raw_score * bar_w) + "." * (bar_w - int(d.raw_score * bar_w))
    print(
        f"  {d.dimension:<25} {d.raw_score:.3f}  [{bar}]  {d.status if hasattr(d, 'status') else ''}"
    )
ScoreCalculator.to_json(breakdown, OUTPUTS / "Score_Breakdown_v2.json")

# ── Phase 10: OutputBuilder ───────────────────────────────────
print("\n[Phase 10] OutputBuilder")
output = OutputBuilder().build(breakdown, issue_summary, sim_log, requirements_full.project_name)
OutputBuilder.to_json(output, OUTPUTS / "Simulation_OUTPUT_v2.json")

# ── 최종 요약 ─────────────────────────────────────────────────
verdict_label = {
    "proceed": "진행 가능",
    "proceed_with_conditions": "조건부 진행",
    "needs_rebalancing": "재조정 필요",
    "not_recommended": "착수 비권장",
}
print("\n" + "=" * 60)
print("  [최종 결과]")
print("=" * 60)
print(f"  overall_project_fit : {output.overall_project_fit:.4f}")
print(
    f"  verdict             : {output.simulation_verdict}  ({verdict_label.get(output.simulation_verdict, '')})"
)
print()
print("  [Top Risks]")
for r in output.top_risks:
    print(f"    #{r.rank} [{r.severity.upper():6s}|{r.status:<9s}] {r.issue_category}")
print()
print("  [Must Fix Before Start]")
if output.must_fix_before_start:
    for m in output.must_fix_before_start:
        print(f"    [{m.severity.upper()}] {m.issue_category}")
        print(f"         {m.suggested_action[:70]}")
else:
    print("    (없음)")
print()
print("  [Phase Stability]")
for ph, sc in output.phase_stability_summary.items():
    bar = "#" * int(sc * 20) + "." * (20 - int(sc * 20))
    print(f"    {ph:<25} {sc:.3f}  [{bar}]")
print()
print(f"  {output.score_note}")
print()
print(f"  출력 폴더: {OUTPUTS}")
for f in sorted(OUTPUTS.glob("*.json")):
    size = f.stat().st_size
    print(f"    {f.name:<40} {size:>8,} bytes")
