"""Phase 6 Role Agent Execution 동작 검증."""

import logging
import pathlib

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.agent_card_builder import (
    AgentCardBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.phase_context_builder import (
    PhaseContextBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.privacy_column_filter import (
    PrivacyColumnFilter,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.scenario_phase_planner import (
    ScenarioPhasePlanner,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.simulation_input_builder import (
    SimulationInputBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.simulation_orchestrator import (
    SimulationOrchestrator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.orchestrator import (
    LLMMode,
    ValidationStatus,
)

samples = pathlib.Path("backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/samples")
outputs = pathlib.Path("backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs")

# Phase 1-4
packet, index = SimulationInputBuilder().build(
    requirements=samples / "sample_requirements_list.json",
    team_record=samples / "sample_selected_team_record.json",
    snapshots=samples / "sample_employee_fit_profile_snapshots.json",
    risk_summary=samples / "sample_team_risk_summary.json",
    evidence_metadata=samples / "sample_evidence_metadata.json",
    simulation_id="sim_p6_demo",
)
result = PrivacyColumnFilter().filter(packet)
cards = AgentCardBuilder().build(result.sanitized_snapshots, packet.project_context)
plan = ScenarioPhasePlanner().plan(
    requirements=packet.project_context,
    risk_summary=packet.team_risk_summary,
    evidence_index=index,
    simulation_id=packet.simulation_id,
)

# Phase 6: Context 생성 및 저장
ctx_builder = PhaseContextBuilder(cards)
all_ctxs = ctx_builder.build_all(plan)
PhaseContextBuilder.to_json(all_ctxs, outputs / "Current_Phase_Context.json")

# Phase 5/6: Orchestrator (PhaseContext 주입)
orch = SimulationOrchestrator(llm_mode=LLMMode.STUB)
output = orch.run(plan, cards)
SimulationOrchestrator.to_json(output, outputs / "Orchestrator_Output.json")

# 검증
print()
print("=" * 70)
print(f"Total contexts : {len(all_ctxs)}")
print(f"Total turns    : {output.total_turns}")
print(f"Total invalid  : {output.total_invalid}")

val_counts = {}
for run in output.phase_runs:
    for t in run.turns:
        val_counts[t.validation.status] = val_counts.get(t.validation.status, 0) + 1
print(f"Validation     : {dict(sorted(val_counts.items()))}")

# Phase 6 상세 — 첫 번째 event turn 상세 출력
print()
print("--- Phase 6 Sample Turn (Integration Phase / evt_009) ---")
target_run = next((r for r in output.phase_runs if r.event_id == "evt_009"), None)
if target_run:
    for turn in target_run.turns:
        print(f"\n[{turn.agent_id} / {turn.assigned_role}]  status={turn.validation.status}")
        print(f"  observation     : {turn.observation}")
        print(f"  concern         : {turn.concern}")
        print(f"  dependency      : {turn.dependency}")
        print(f"  proposed_action : {turn.proposed_action}")
        print(f"  evidence_used   : {turn.evidence_refs_used}")
        if turn.validation.status != ValidationStatus.VALID:
            print(f"  [!] {turn.validation.reason}")

# Pass 기준
p6_pass = len(all_ctxs) > 0 and output.total_turns > 0 and output.total_invalid == 0
print()
print(f">>> Phase 6 {'PASS' if p6_pass else 'FAIL'}")
print(f"    contexts={len(all_ctxs)} turns={output.total_turns} invalid={output.total_invalid}")
