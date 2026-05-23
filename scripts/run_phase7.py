"""Phase 7 검증 스크립트

Phases 1-6을 재실행한 뒤 PhaseLogCollector로 Team_Simulation_Log.json을 생성하고
기본 지표를 콘솔에 출력한다.
"""

import json
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules import (
    AgentCardBuilder,
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

# ── Phase 1 ──────────────────────────────────
print("=== Phase 1: SimulationInputBuilder ===")
builder = SimulationInputBuilder()
packet, evidence_index = builder.build(
    requirements=SAMPLES / "sample_requirements_list.json",
    team_record=SAMPLES / "sample_selected_team_record.json",
    snapshots=SAMPLES / "sample_employee_fit_profile_snapshots.json",
    risk_summary=SAMPLES / "sample_team_risk_summary.json",
    evidence_metadata=SAMPLES / "sample_evidence_metadata.json",
)
print(f"  project_name = {packet.project_context.project_name}")

# 이후 phase에서 직접 사용할 파싱 객체
requirements = packet.project_context  # RequirementsList는 project_context에 내포됨
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
# RequirementsList 직접 로드 (planner/collector용)
requirements_full = RequirementsList.model_validate(
    json.loads((SAMPLES / "sample_requirements_list.json").read_text(encoding="utf-8"))
)

# ── Phase 2 ───────────────────────────────────
print("=== Phase 2: PrivacyColumnFilter ===")
pcf = PrivacyColumnFilter()
result = pcf.filter(packet)
print(f"  sanitized snapshots: {len(result.sanitized_snapshots)}")

# ── Phase 3 ───────────────────────────────────
print("=== Phase 3: AgentCardBuilder ===")
card_builder = AgentCardBuilder()
agent_cards = card_builder.build(result.sanitized_snapshots, requirements_full)
print(f"  agent cards: {len(agent_cards)}")

# ── Phase 4 ───────────────────────────────────
print("=== Phase 4: ScenarioPhasePlanner ===")
planner = ScenarioPhasePlanner()
plan = planner.plan(
    requirements_full, risk_summary, evidence_index, simulation_id="sim_phase7_test"
)
total_events = sum(len(p.scenario_events) for p in plan.phases)
print(f"  phases: {len(plan.phases)}, total events: {total_events}")

# ── Phase 5/6 ────────────────────────────────
print("=== Phase 5/6: SimulationOrchestrator + RoleAgent ===")
orchestrator = SimulationOrchestrator(llm_mode="stub")
orch_output = orchestrator.run(plan, agent_cards)
total_turns = sum(len(r.turns) for r in orch_output.phase_runs)
print(f"  phase_runs: {len(orch_output.phase_runs)}, total turns: {total_turns}")

# ── Phase 7 ──────────────────────────────────
print("\n=== Phase 7: PhaseLogCollector ===")
collector = PhaseLogCollector()
sim_log = collector.collect(orch_output, plan, requirements_full, team, save_raw=False)

# 저장
out_path = OUTPUTS / "Team_Simulation_Log.json"
PhaseLogCollector.to_json(sim_log, out_path)

# ── 출력 요약 ─────────────────────────────────
print("\n[Team_Simulation_Log 요약]")
print(f"  simulation_id : {sim_log.simulation_id}")
print(f"  project_name  : {sim_log.project_name}")
print(f"  team_id       : {sim_log.team_id}")
print(f"  phases        : {len(sim_log.phase_logs)}")
print(f"  total_issues  : {sim_log.total_issues}")
print(f"  total_actions : {sim_log.total_actions}")
print(f"  total_unresolved: {sim_log.total_unresolved}")
print()

for plog in sim_log.phase_logs:
    sc = plog.phase_scores
    print(
        f"  [{plog.phase_name}] "
        f"turns={len(plog.participant_turns)} "
        f"issues={len(plog.detected_issues)} "
        f"actions={len(plog.action_items)} "
        f"unresolved={len(plog.unresolved_questions)} "
        f"stability={sc.phase_stability_score if sc else 'N/A'}"
    )

print(f"\n=> Team_Simulation_Log.json saved: {out_path}")
