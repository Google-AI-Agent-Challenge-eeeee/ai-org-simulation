"""Phase 10 검증 스크립트

Phases 1-9를 재실행한 뒤 OutputBuilder로 Simulation_OUTPUT.json을 생성하고
최종 결과를 콘솔에 출력한다.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# .env 로드
_env_file = ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

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

SAMPLES = ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/samples"
OUTPUTS = ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs"

# ── Phase 1-6 ─────────────────────────────────
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
result = PrivacyColumnFilter().filter(packet)
cards = AgentCardBuilder().build(result.sanitized_snapshots, requirements_full)
plan = ScenarioPhasePlanner().plan(
    requirements_full, risk_summary, evidence_index, simulation_id="sim_final_test"
)
orch_out = SimulationOrchestrator(llm_mode="vertex").run(plan, cards)
total_turns = sum(len(r.turns) for r in orch_out.phase_runs)
print(f"  turns={total_turns}")

# ── Gemini 대화 출력 ────────────────────────────
print()
print("=" * 60)
print("  GEMINI 시뮬레이션 대화 로그")
print("=" * 60)
current_phase = None
for run in orch_out.phase_runs:
    phase_label = run.phase_name if hasattr(run, "phase_name") else ""
    if phase_label != current_phase:
        current_phase = phase_label
        print(f"\n{'─' * 60}")
        print(f"  PHASE: {current_phase}")
        print(f"{'─' * 60}")
    print(f"\n  [Event: {run.event_id}] {run.event_desc[:60]}...")
    for turn in run.turns:
        status = turn.validation.status if turn.validation else "?"
        print(f"\n    [{turn.agent_id} / {turn.assigned_role}]  [{status}]")
        print(f"      observation    : {turn.observation}")
        print(f"      concern        : {turn.concern}")
        print(f"      dependency     : {turn.dependency}")
        print(f"      proposed_action: {turn.proposed_action}")
        if turn.evidence_refs_used:
            print(f"      evidence_used  : {turn.evidence_refs_used}")
print()
print("=" * 60)

# ── Phase 7 ───────────────────────────────────
print("=== Phase 7: PhaseLogCollector ===")
sim_log = PhaseLogCollector().collect(orch_out, plan, requirements_full, team)

# ── Phase 8 ───────────────────────────────────
print("=== Phase 8: IssueRiskEvaluator ===")
issue_summary = IssueRiskEvaluator().evaluate(sim_log, risk_summary, evidence_list)

# ── Phase 9 ───────────────────────────────────
print("=== Phase 9: ScoreCalculator ===")
breakdown = ScoreCalculator().calculate(issue_summary, sim_log)

# ── Phase 10 ──────────────────────────────────
print("\n=== Phase 10: OutputBuilder ===")
ob = OutputBuilder()
output = ob.build(breakdown, issue_summary, sim_log, requirements_full.project_name)

out_path = OUTPUTS / "Simulation_OUTPUT.json"
OutputBuilder.to_json(output, out_path)

# ── 출력 ──────────────────────────────────────
verdict_label = {
    "proceed": "진행 가능",
    "proceed_with_conditions": "조건부 진행",
    "needs_rebalancing": "재조정 필요",
    "not_recommended": "착수 비권장",
}

print(f"\n{'=' * 60}")
print("  [최종 Simulation_OUTPUT]")
print(f"{'=' * 60}")
print(f"  simulation_id       : {output.simulation_id}")
print(f"  project_name        : {output.project_name}")
print(f"  team_id             : {output.team_id}")
print(f"  overall_project_fit : {output.overall_project_fit:.4f}")
print(
    f"  verdict             : {output.simulation_verdict}  ({verdict_label.get(output.simulation_verdict, '')})"
)
print()
print("[Score Breakdown]")
for d in output.score_breakdown:
    bar = "#" * int(d.raw_score * 20) + "." * (20 - int(d.raw_score * 20))
    print(f"  {d.dimension:<25} {d.raw_score:.3f}  [{bar}]  {d.status}")

print()
print("[Top Risks]")
for r in output.top_risks:
    print(f"  #{r.rank} [{r.severity.upper():6s}|{r.status:<9s}] {r.issue_category}")
    print(f"       phases: {r.observed_in_phases}")
    print(f"       action: {r.suggested_action[:70]}")

print()
print("[Must Fix Before Start]")
if output.must_fix_before_start:
    for m in output.must_fix_before_start:
        print(f"  [{m.severity.upper()}] {m.issue_category}")
        print(f"       roles  : {m.affected_roles}")
        print(f"       action : {m.suggested_action[:70]}")
else:
    print("  (없음)")

print()
print("[Evidence Summary]")
print(f"  evidence refs used  : {output.evidence_summary.total_evidence_refs}")
print(f"  confirmed issues    : {output.evidence_summary.total_confirmed_issues}")
print(f"  candidate issues    : {output.evidence_summary.total_candidate_issues}")
print(f"  unresolved turns    : {output.evidence_summary.total_unresolved_turns}")
print(f"  high-risk phases    : {output.evidence_summary.phases_with_high_risk}")

print()
print("[Phase Stability]")
for ph, sc in output.phase_stability_summary.items():
    bar = "#" * int(sc * 20) + "." * (20 - int(sc * 20))
    print(f"  {ph:<25} {sc:.3f}  [{bar}]")

print()
print("[Score Note]")
print(f"  {output.score_note}")

print(f"\n=> Simulation_OUTPUT.json saved: {out_path}")
