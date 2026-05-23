"""Vertex AI Gemini LLM 모드 테스트 스크립트

.env의 LLM_MODE=vertex, GCP_PROJECT_ID 값을 읽어
Kickoff 단계의 첫 번째 에이전트 1턴만 Gemini로 실행한다.

실행:
    uv run python scripts/run_llm.py
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# .env 로드 (python-dotenv 없을 경우 수동 파싱)
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules import (
    AgentCardBuilder,
    PhaseContextBuilder,
    PrivacyColumnFilter,
    ScenarioPhasePlanner,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline import (
    SimulationInputBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.role_agent import (
    RoleAgent,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.orchestrator import (
    LLMMode,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    RequirementsList,
    TeamRiskSummary,
)

SAMPLES = ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/samples"

print("=" * 60)
print("  Vertex AI Gemini LLM Integration Test")
print("=" * 60)
print(f"  GCP_PROJECT_ID  : {os.environ.get('GCP_PROJECT_ID', '(not set)')}")
print(f"  VERTEX_LOCATION : {os.environ.get('VERTEX_LOCATION', 'asia-northeast3')}")
print(f"  VERTEX_MODEL    : {os.environ.get('VERTEX_MODEL', 'gemini-2.5-flash')}")
print()

# Phase 1 — 입력 병합
print("[Phase 1] Building simulation input packet...")
builder = SimulationInputBuilder()
packet, evidence_index = builder.build(
    requirements=SAMPLES / "sample_requirements_list.json",
    team_record=SAMPLES / "sample_selected_team_record.json",
    snapshots=SAMPLES / "sample_employee_fit_profile_snapshots.json",
    risk_summary=SAMPLES / "sample_team_risk_summary.json",
    evidence_metadata=SAMPLES / "sample_evidence_metadata.json",
)
print(f"  members={len(packet.member_snapshots)}, evidence_items={len(evidence_index.by_id)}")

# Phase 2 — Privacy Filter
print("[Phase 2] Filtering personal data...")
requirements_full = RequirementsList.model_validate(
    json.loads((SAMPLES / "sample_requirements_list.json").read_text(encoding="utf-8"))
)
risk_summary = TeamRiskSummary.model_validate(
    json.loads((SAMPLES / "sample_team_risk_summary.json").read_text(encoding="utf-8"))
)
result = PrivacyColumnFilter().filter(packet)

# Phase 3 — Agent Cards
print("[Phase 3] Building agent cards...")
cards = AgentCardBuilder().build(result.sanitized_snapshots, requirements_full)
print(f"  cards={[c.agent_id for c in cards]}")

# Phase 4 — Phase Plan
print("[Phase 4] Planning simulation phases...")
plan = ScenarioPhasePlanner().plan(
    requirements_full, risk_summary, evidence_index, simulation_id="sim_llm_test"
)
kickoff = plan.phases[0]
print(f"  Kickoff events={len(kickoff.scenario_events)}")

# Phase 6 — LLM 모드 에이전트 발언 (Kickoff 첫 번째 이벤트, 첫 번째 에이전트)
print()
print("[Phase 6] LLM agent turn — calling Gemini...")
first_card = cards[0]
first_event = kickoff.scenario_events[0]

ctx_builder = PhaseContextBuilder(cards)
ctx = ctx_builder.build(
    phase=kickoff,
    event=first_event,
    agent_role=first_card.assigned_role,
)

agent = RoleAgent(card=first_card, llm_mode=LLMMode.VERTEX)
turn = agent.speak_with_context(ctx)

print()
print(f"  Agent      : {turn.agent_id}")
print(f"  Role       : {turn.assigned_role}")
print(f"  LLM Mode   : {turn.llm_mode}")
print(f"  Validation : {turn.validation.status if turn.validation else 'N/A'}")
print()
print("  --- observation ---")
print(f"  {turn.observation}")
print()
print("  --- concern ---")
print(f"  {turn.concern}")
print()
print("  --- dependency ---")
print(f"  {turn.dependency}")
print()
print("  --- proposed_action ---")
print(f"  {turn.proposed_action}")
print()
print("  --- evidence_refs_used ---")
print(f"  {turn.evidence_refs_used}")
print()
print("  Validation details:", turn.validation)
print()
print("=" * 60)
print("  LLM test DONE")
print("=" * 60)
