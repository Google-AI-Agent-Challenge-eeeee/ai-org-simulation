"""Phase 1~4 통합 점검 스크립트."""

import logging
import pathlib

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

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

samples = pathlib.Path("backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/samples")
outputs = pathlib.Path("backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs")

# ──────────────────────────────────────────────
# Phase 1: Simulation Input Builder
# ──────────────────────────────────────────────
packet, index = SimulationInputBuilder().build(
    requirements=samples / "sample_requirements_list.json",
    team_record=samples / "sample_selected_team_record.json",
    snapshots=samples / "sample_employee_fit_profile_snapshots.json",
    risk_summary=samples / "sample_team_risk_summary.json",
    evidence_metadata=samples / "sample_evidence_metadata.json",
    simulation_id="sim_full_check",
)
SimulationInputBuilder.to_json(packet, outputs / "Simulation_Input_Packet.json")

uncovered = sorted(set(packet.team_risk_summary.risk_tags) - set(index.by_risk_tag.keys()))
p1_pass = (
    len(packet.selected_team.members) == 5
    and len(packet.member_snapshots) == 5
    and len(packet.evidence_metadata) >= 11
    and len(uncovered) == 0
)
status = "PASS" if p1_pass else "FAIL"
print(
    f"Phase 1 | InputBuilder   | members={len(packet.selected_team.members)} evidence={len(packet.evidence_metadata)} uncovered={uncovered} | {status}"
)

# ──────────────────────────────────────────────
# Phase 2: Privacy & Column Filter
# ──────────────────────────────────────────────
result = PrivacyColumnFilter().filter(packet)
PrivacyColumnFilter.to_json(result.sanitized_snapshots, outputs / "Sanitized_Profile_Snapshot.json")

p2_pass = all(
    "employee_id" not in s.model_dump() and len(s.model_dump()) == 10
    for s in result.sanitized_snapshots
)
removed = PrivacyColumnFilter.removed_fields()
retained = PrivacyColumnFilter.retained_fields()
status = "PASS" if p2_pass else "FAIL"
print(
    f"Phase 2 | PrivacyFilter  | sanitized={len(result.sanitized_snapshots)} removed={removed} retained={len(retained)} fields | {status}"
)

# ──────────────────────────────────────────────
# Phase 3: Agent Card Builder
# ──────────────────────────────────────────────
cards = AgentCardBuilder().build(result.sanitized_snapshots, packet.project_context)
AgentCardBuilder.to_json(cards, outputs / "Agent_Cards.json")

p3_pass = (
    len(cards) == 5
    and all(not c.agent_id.startswith("E2026") for c in cards)
    and all(len(c.speaking_rules) == 5 for c in cards)
    and all(len(c.responsibilities) > 0 for c in cards)
    and all(len(c.constraints) > 0 for c in cards)
)
status = "PASS" if p3_pass else "FAIL"
print(
    f"Phase 3 | AgentCardBuild | cards={len(cards)} agent_ids={[c.agent_id for c in cards]} | {status}"
)

# ──────────────────────────────────────────────
# Phase 4: Scenario Phase Planner
# ──────────────────────────────────────────────
plan = ScenarioPhasePlanner().plan(
    requirements=packet.project_context,
    risk_summary=packet.team_risk_summary,
    evidence_index=index,
    simulation_id=packet.simulation_id,
)
ScenarioPhasePlanner.to_json(plan, outputs / "Simulation_Phase_Plan.json")

total_events = sum(len(p.scenario_events) for p in plan.phases)
p4_pass = (
    len(plan.phases) == 5
    and total_events > 0
    and all(len(p.agenda) > 0 for p in plan.phases)
    and all(len(p.scenario_events) > 0 for p in plan.phases)
)
status = "PASS" if p4_pass else "FAIL"
print(
    f"Phase 4 | PhasePlanner   | phases={len(plan.phases)} total_events={total_events} | {status}"
)

# ──────────────────────────────────────────────
# 상세 리포트
# ──────────────────────────────────────────────
print()
print("=" * 60)
print("Phase 1  Simulation Input Packet")
print("=" * 60)
print(f"  sim_id    : {packet.simulation_id}")
print(f"  project   : {packet.project_context.project_name}")
print(
    f"  team_id   : {packet.selected_team.team_id}  fit_score={packet.selected_team.team_fit_score}"
)
for m in packet.selected_team.members:
    print(f"    {m.employee_id}  {m.employee_name:5s}  {m.assigned_role}")
print(f"  risk_tags : {packet.team_risk_summary.risk_tags}")
print(f"  evidence  : {len(packet.evidence_metadata)} entries")

print()
print("=" * 60)
print("Phase 2  Sanitized Profile Snapshot")
print("=" * 60)
print(f"  removed fields : {removed}")
for s in result.sanitized_snapshots:
    print(
        f"  {s.employee_name:5s} | {s.assigned_role:20s} | "
        f"cap={s.capacity_signal:11s} comm={s.communication_signal:12s} "
        f"del={s.delivery_signal:8s} collab={s.collaboration_signal}"
    )

print()
print("=" * 60)
print("Phase 3  Agent Cards")
print("=" * 60)
for c in cards:
    print(f"  [{c.agent_id}]  role={c.assigned_role}")
    print(f"    responsibilities : {c.responsibilities}")
    print(f"    strengths        : {c.strengths}")
    print(f"    constraints      : {c.constraints}")
    print(f"    risk_tags        : {c.risk_tags}")
    print(f"    evidence_refs    : {c.evidence_refs}")

print()
print("=" * 60)
print("Phase 4  Simulation Phase Plan")
print("=" * 60)
for p in plan.phases:
    print(f"  [{p.phase_name.value}]  agenda={len(p.agenda)}  events={len(p.scenario_events)}")
    print(f"    focus_risks : {p.focus_risk_tags}")
    for ev in p.scenario_events:
        print(f"    [{ev.event_id}] {ev.expected_issue_category}")
        print(f"      desc    : {ev.description[:70]}...")
        print(f"      trigger : {ev.trigger_source}")
        print(f"      roles   : {ev.involved_roles}")

print()
overall = "ALL PASS" if all([p1_pass, p2_pass, p3_pass, p4_pass]) else "SOME FAIL"
print(f">>> {overall}")
