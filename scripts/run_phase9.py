"""Phase 9 검증 스크립트

Phases 1-8을 재실행한 뒤 ScoreCalculator로 Score_Breakdown.json을 생성하고
차원별 점수와 overall_project_fit을 출력한다.
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
pcf = PrivacyColumnFilter()
result = pcf.filter(packet)
cards = AgentCardBuilder().build(result.sanitized_snapshots, requirements_full)
plan = ScenarioPhasePlanner().plan(
    requirements_full, risk_summary, evidence_index, simulation_id="sim_phase9_test"
)
orch_output = SimulationOrchestrator(llm_mode="stub").run(plan, cards)
print(
    f"  phase_runs={len(orch_output.phase_runs)} turns={sum(len(r.turns) for r in orch_output.phase_runs)}"
)

# ── Phase 7 ───────────────────────────────────
print("=== Phase 7: PhaseLogCollector ===")
sim_log = PhaseLogCollector().collect(orch_output, plan, requirements_full, team)
print(f"  issues={sim_log.total_issues} unresolved={sim_log.total_unresolved}")

# ── Phase 8 ───────────────────────────────────
print("=== Phase 8: IssueRiskEvaluator ===")
issue_summary = IssueRiskEvaluator().evaluate(sim_log, risk_summary, evidence_list)
print(
    f"  confirmed={issue_summary.total_confirmed} "
    f"candidate={issue_summary.total_candidate} "
    f"invalid={issue_summary.total_invalid}"
)

# ── Phase 9 ───────────────────────────────────
print("\n=== Phase 9: ScoreCalculator ===")
calc = ScoreCalculator()
breakdown = calc.calculate(issue_summary, sim_log)

out_path = OUTPUTS / "Score_Breakdown.json"
ScoreCalculator.to_json(breakdown, out_path)

# ── 출력 요약 ─────────────────────────────────
print("\n[Score_Breakdown 요약]")
print(f"  simulation_id        : {breakdown.simulation_id}")
print(f"  overall_project_fit  : {breakdown.overall_project_fit:.4f}")
print(f"  verdict              : {breakdown.verdict}")
print(f"  must_fix_categories  : {breakdown.must_fix_categories}")
print(f"  top_risk_dimensions  : {breakdown.top_risk_dimensions}")
print()

bar_width = 30
print(f"  {'Dimension':<25} {'Weight':>6}  {'Raw':>5}  {'Weighted':>8}  Score bar")
print(f"  {'-' * 25} {'-' * 6}  {'-' * 5}  {'-' * 8}  {'-' * bar_width}")
for d in breakdown.dimensions:
    filled = int(d.raw_score * bar_width)
    bar = "#" * filled + "." * (bar_width - filled)
    print(
        f"  {d.dimension:<25} {d.weight:>6.2f}  {d.raw_score:>5.3f}  {d.weighted_score:>8.4f}  [{bar}]"
    )

print()
print(f"  {'overall_project_fit':.<40} {breakdown.overall_project_fit:.4f}")
print()
print("[Score Note]")
print(f"  {breakdown.score_note}")
print(f"\n=> Score_Breakdown.json saved: {out_path}")
