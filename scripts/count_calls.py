import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
plan = json.loads(
    (ROOT / "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs/Simulation_Phase_Plan.json")
    .read_text(encoding="utf-8")
)

total_calls = 0
print("Phase별 이벤트 x 참여 역할 수:")
for phase in plan["phases"]:
    events = phase["scenario_events"]
    phase_calls = sum(len(evt["involved_roles"]) for evt in events)
    total_calls += phase_calls
    print(f"\n  [{phase['phase_name']}]  이벤트 {len(events)}개  →  {phase_calls}회 호출")
    for evt in events:
        roles = ", ".join(evt["involved_roles"])
        print(f"    {evt['event_id']}: [{roles}]  ({len(evt['involved_roles'])}명)")

print(f"\n{'='*50}")
print(f"  기본 호출 합계          : {total_calls}회")
print(f"  재질문(_MAX_RETRY=1) 최대: {total_calls * 2}회")
print(f"  (재질문은 INVALID/NEEDS_RETRY 발언에만 발생)")
