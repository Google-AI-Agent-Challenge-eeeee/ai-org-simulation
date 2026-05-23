"""Phase 8 검증 스크립트

Phases 1-7을 재실행한 뒤 IssueRiskEvaluator로 Issue_Risk_Summary.json을 생성하고
기본 지표를 콘솔에 출력한다.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules import (
    AgentCardBuilder,
    IssueRiskEvaluator,
    PhaseLogCollector,
    PrivacyColumnFilter,
    ScenarioPhasePlanner,
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

SAMPLES = ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/samples"
OUTPUTS = ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs"

# ── Phase 1 ───────────────────────────────────
print("=== Phase 1-6: Pipeline ===")
builder = SimulationInputBuilder()
packet, evidence_index = builder.build(
    requirements=SAMPLES / "sample_requirements_list.json",
    team_record=SAMPLES / "sample_selected_team_record.json",
    snapshots=SAMPLES / "sample_employee_fit_profile_snapshots.json",
    risk_summary=SAMPLES / "sample_team_risk_summary.json",
    evidence_metadata=SAMPLES / "sample_evidence_metadata.json",
)

requirements_full = RequirementsList.model_validate(
    json.loads((SAMPLES / "sample_requirements_list.json").read_text(encoding="utf-8"))
)
team = SelectedTeamRecord.model_validate(
    json.loads((SAMPLES / "sample_selected_team_record.json").read_text(encoding="utf-8"))
)
risk_summary = TeamRiskSummary.model_validate(
    json.loads((SAMPLES / "sample_team_risk_summary.json").read_text(encoding="utf-8"))
)
evidence_list = [
    EvidenceMetadata.model_validate(e)
    for e in json.loads((SAMPLES / "sample_evidence_metadata.json").read_text(encoding="utf-8"))
]

pcf = PrivacyColumnFilter()
result = pcf.filter(packet)

card_builder = AgentCardBuilder()
agent_cards = card_builder.build(result.sanitized_snapshots, requirements_full)

planner = ScenarioPhasePlanner()
plan = planner.plan(
    requirements_full, risk_summary, evidence_index, simulation_id="sim_phase8_test"
)

orchestrator = SimulationOrchestrator(llm_mode="stub")
orch_output = orchestrator.run(plan, agent_cards)

# ── Phase 7 ───────────────────────────────────
print("=== Phase 7: PhaseLogCollector ===")
collector = PhaseLogCollector()
sim_log = collector.collect(orch_output, plan, requirements_full, team, save_raw=False)
print(
    f"  phases={len(sim_log.phase_logs)} "
    f"issues={sim_log.total_issues} "
    f"actions={sim_log.total_actions} "
    f"unresolved={sim_log.total_unresolved}"
)

# ── Phase 8 ───────────────────────────────────
print("\n=== Phase 8: IssueRiskEvaluator ===")
evaluator = IssueRiskEvaluator()
issue_summary = evaluator.evaluate(sim_log, risk_summary, evidence_list)

out_path = OUTPUTS / "Issue_Risk_Summary.json"
IssueRiskEvaluator.to_json(issue_summary, out_path)

# ── 출력 요약 ─────────────────────────────────
print("\n[Issue_Risk_Summary 요약]")
print(f"  simulation_id    : {issue_summary.simulation_id}")
print(f"  team_id          : {issue_summary.team_id}")
print(f"  confirmed issues : {issue_summary.total_confirmed}")
print(f"  candidate issues : {issue_summary.total_candidate}")
print(f"  invalid  issues  : {issue_summary.total_invalid}")
print(
    f"  HIGH / MEDIUM / LOW : {issue_summary.high_count} / {issue_summary.medium_count} / {issue_summary.low_count}"
)

print("\n[CONFIRMED 목록]")
for ci in issue_summary.confirmed_issues:
    print(
        f"  [{ci.severity.upper():6s}] {ci.issue_category:<30s} "
        f"score={ci.final_issue_score:.3f}  "
        f"pre={ci.pre_simulation_risk:.2f}  obs={ci.observed_simulation_risk:.2f}  "
        f"phases={ci.observed_in_phases}"
    )

if issue_summary.candidate_issues:
    print("\n[CANDIDATE 목록]")
    for ci in issue_summary.candidate_issues:
        print(
            f"  [{ci.severity.upper():6s}] {ci.issue_category:<30s} "
            f"score={ci.final_issue_score:.3f}"
        )

print(f"\n=> Issue_Risk_Summary.json saved: {out_path}")
