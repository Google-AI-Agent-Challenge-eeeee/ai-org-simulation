"""Phase 5/6 Simulation Orchestrator 동작 검증."""

import logging
import pathlib

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.agent_card_builder import (
    AgentCardBuilder,
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

# Phase 1–4
packet, index = SimulationInputBuilder().build(
    requirements=samples / "sample_requirements_list.json",
    team_record=samples / "sample_selected_team_record.json",
    snapshots=samples / "sample_employee_fit_profile_snapshots.json",
    risk_summary=samples / "sample_team_risk_summary.json",
    evidence_metadata=samples / "sample_evidence_metadata.json",
    simulation_id="sim_orch_demo",
)
result = PrivacyColumnFilter().filter(packet)
cards = AgentCardBuilder().build(result.sanitized_snapshots, packet.project_context)
plan = ScenarioPhasePlanner().plan(
    requirements=packet.project_context,
    risk_summary=packet.team_risk_summary,
    evidence_index=index,
    simulation_id=packet.simulation_id,
)

# Phase 5/6
orch = SimulationOrchestrator(llm_mode=LLMMode.STUB)
output = orch.run(plan, cards)
SimulationOrchestrator.to_json(output, outputs / "Orchestrator_Output.json")

# 결과 출력
print()
print("=" * 70)
print(f"simulation_id : {output.simulation_id}")
print(f"llm_mode      : {output.llm_mode}")
print(f"total_turns   : {output.total_turns}")
print(f"total_invalid : {output.total_invalid}")
print()

validation_counts = {}
for run in output.phase_runs:
    for turn in run.turns:
        s = turn.validation.status
        validation_counts[s] = validation_counts.get(s, 0) + 1

print("Validation 분포:", dict(sorted(validation_counts.items())))
print()

current_phase = None
for run in output.phase_runs:
    if run.phase_name != current_phase:
        current_phase = run.phase_name
        print(f"\n{'=' * 70}")
        print(f"[{run.phase_name}]")

    print(f"\n  <{run.event_id}> trigger={run.trigger_source}")
    for turn in run.turns:
        status = turn.validation.status
        print(f"  [{turn.agent_id} / {turn.assigned_role}] status={status}")
        print(f"    observation     : {turn.observation[:80]}...")
        print(f"    concern         : {turn.concern[:80]}...")
        print(f"    dependency      : {turn.dependency[:80]}...")
        print(f"    proposed_action : {turn.proposed_action[:80]}...")
        print(f"    evidence_used   : {turn.evidence_refs_used}")
        if turn.validation.status != ValidationStatus.VALID:
            print(f"    [!] {turn.validation.reason}")

    if run.flags:
        for flag in run.flags:
            print(f"  [FLAG/{flag.flag_type}] {flag.agent_id}: {flag.message[:80]}")

# 최종 검증
total_events = sum(len(p.scenario_events) for p in plan.phases)
p5_pass = (
    output.total_turns > 0
    and len(output.phase_runs) == total_events
    and output.llm_mode == LLMMode.STUB
)
print()
print(f">>> Phase 5/6 {'PASS' if p5_pass else 'FAIL'}")
print(f"    phase_runs={len(output.phase_runs)} / expected={total_events}")
print(f"    total_turns={output.total_turns}  invalid={output.total_invalid}")
