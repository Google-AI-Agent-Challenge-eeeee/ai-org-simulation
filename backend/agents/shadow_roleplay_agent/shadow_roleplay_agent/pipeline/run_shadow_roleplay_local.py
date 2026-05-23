"""Local CLI runner for Shadow RolePlay simulation from a Requirements packet."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.agent_card_builder import (
    AgentCardBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.issue_risk_evaluator import (
    IssueRiskEvaluator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.output_builder import (
    OutputBuilder,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.phase_log_collector import (
    PhaseLogCollector,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.privacy_column_filter import (
    PrivacyColumnFilter,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.scenario_phase_planner import (
    ScenarioPhasePlanner,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.modules.score_calculator import (
    ScoreCalculator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.simulation_input_builder import (
    EvidenceIndex,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.simulation_orchestrator import (
    SimulationOrchestrator,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.orchestrator import (
    LLMMode,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    SimulationInputPacket,
)

JsonObject = dict[str, Any]

DEFAULT_INPUT_PACKET = Path(
    "backend/agents/requirements_agent/outputs/Roleplay_Simulation_Input_Packet.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "backend/agents/shadow_roleplay_agent/shadow_roleplay_agent/outputs/local_prd_001"
)

OUTPUT_FILENAMES = {
    "sanitized_profile_snapshot": "Sanitized_Profile_Snapshot.json",
    "agent_cards": "Agent_Cards.json",
    "simulation_phase_plan": "Simulation_Phase_Plan.json",
    "orchestrator_output": "Orchestrator_Output.json",
    "team_simulation_log": "Team_Simulation_Log.json",
    "issue_risk_summary": "Issue_Risk_Summary.json",
    "score_breakdown": "Score_Breakdown.json",
    "simulation_output": "Simulation_OUTPUT.json",
}

SUPPORTED_ROLEPLAY_LLM_MODES = {mode.value for mode in LLMMode}


def run_local_shadow_roleplay(
    *,
    input_packet_path: str | Path = DEFAULT_INPUT_PACKET,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    llm_mode: str = "stub",
    strict_llm: bool = False,
    write_outputs: bool = False,
) -> JsonObject:
    """Run the local Shadow RolePlay pipeline from a simulation input packet."""

    packet = _load_packet(input_packet_path)
    return run_local_shadow_roleplay_from_packet(
        packet,
        input_packet_label=str(Path(input_packet_path)),
        output_dir=output_dir,
        llm_mode=llm_mode,
        strict_llm=strict_llm,
        write_outputs=write_outputs,
    )


def run_local_shadow_roleplay_from_packet(
    packet: SimulationInputPacket | Mapping[str, Any],
    *,
    input_packet_label: str = "memory://roleplay_simulation_input_packet",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    llm_mode: str = "stub",
    strict_llm: bool = False,
    write_outputs: bool = False,
) -> JsonObject:
    """Run Shadow RolePlay from an in-memory simulation packet."""

    packet = SimulationInputPacket.model_validate(packet)
    mode = LLMMode(llm_mode)
    evidence_index = EvidenceIndex.build(packet.evidence_metadata)
    sanitized = PrivacyColumnFilter().filter(packet)
    cards = AgentCardBuilder().build(sanitized.sanitized_snapshots, packet.project_context)
    phase_plan = ScenarioPhasePlanner().plan(
        packet.project_context,
        packet.team_risk_summary,
        evidence_index,
        packet.simulation_id,
    )
    orchestrator_output = SimulationOrchestrator(mode, strict_llm=strict_llm).run(
        phase_plan,
        cards,
    )
    simulation_log = PhaseLogCollector().collect(
        orchestrator_output,
        phase_plan,
        packet.project_context,
        packet.selected_team,
    )
    issue_summary = IssueRiskEvaluator().evaluate(
        simulation_log,
        packet.team_risk_summary,
        packet.evidence_metadata,
    )
    score_breakdown = ScoreCalculator().calculate(issue_summary, simulation_log)
    final_output = OutputBuilder().build(
        score_breakdown,
        issue_summary,
        simulation_log,
        packet.project_context.project_name,
    )

    outputs = {
        "sanitized_profile_snapshot": [
            snapshot.model_dump(mode="json") for snapshot in sanitized.sanitized_snapshots
        ],
        "agent_cards": [card.model_dump(mode="json") for card in cards],
        "simulation_phase_plan": phase_plan.model_dump(mode="json"),
        "orchestrator_output": orchestrator_output.model_dump(mode="json"),
        "team_simulation_log": simulation_log.model_dump(mode="json"),
        "issue_risk_summary": issue_summary.model_dump(mode="json"),
        "score_breakdown": score_breakdown.model_dump(mode="json"),
        "simulation_output": final_output.model_dump(mode="json"),
    }
    written_files = _write_outputs(outputs, output_dir) if write_outputs else []
    scenario_event_count = sum(len(phase.scenario_events) for phase in phase_plan.phases)

    return {
        "summary": {
            "roleplay_status": "completed",
            "input_packet": input_packet_label,
            "roleplay_output_dir": str(Path(output_dir)),
            "llm_mode": mode.value,
            "strict_llm": strict_llm,
            "actual_llm_mode": orchestrator_output.actual_llm_mode,
            "vertex_turn_count": orchestrator_output.vertex_turn_count,
            "fallback_count": orchestrator_output.fallback_count,
            "phase_count": len(phase_plan.phases),
            "scenario_event_count": scenario_event_count,
            "orchestrator_phase_run_count": len(orchestrator_output.phase_runs),
            "team_simulation_phase_log_count": len(simulation_log.phase_logs),
            "confirmed_issue_count": issue_summary.total_confirmed,
            "candidate_issue_count": issue_summary.total_candidate,
            "overall_project_fit": final_output.overall_project_fit,
            "verdict": str(final_output.simulation_verdict),
            "write_outputs": write_outputs,
            "written_file_count": len(written_files),
        },
        "outputs": outputs,
        "written_files": written_files,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Shadow RolePlay locally from Roleplay_Simulation_Input_Packet.json."
    )
    parser.add_argument(
        "--input-packet",
        default=str(DEFAULT_INPUT_PACKET),
        help="Path to Roleplay_Simulation_Input_Packet.json.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for local Shadow RolePlay outputs.",
    )
    parser.add_argument(
        "--llm-mode",
        default=LLMMode.STUB.value,
        choices=sorted(SUPPORTED_ROLEPLAY_LLM_MODES),
        help="Shadow RolePlay orchestrator mode.",
    )
    parser.add_argument(
        "--strict-llm",
        action="store_true",
        help="Fail if remote LLM mode cannot produce valid turns instead of falling back to stub.",
    )
    parser.add_argument(
        "--write-outputs",
        action="store_true",
        help="Write Simulation_OUTPUT.json and intermediate local outputs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_local_shadow_roleplay(
        input_packet_path=args.input_packet,
        output_dir=args.output_dir,
        llm_mode=args.llm_mode,
        strict_llm=args.strict_llm,
        write_outputs=args.write_outputs,
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    if result["written_files"]:
        print(json.dumps({"written_files": result["written_files"]}, ensure_ascii=False, indent=2))
    return 0


def _load_packet(path: str | Path) -> SimulationInputPacket:
    with Path(path).open(encoding="utf-8") as f:
        return SimulationInputPacket.model_validate(json.load(f))


def _write_outputs(outputs: Mapping[str, Any], output_dir: str | Path) -> list[str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    written_files = []
    for key, filename in OUTPUT_FILENAMES.items():
        path = root / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(outputs[key], f, ensure_ascii=False, indent=2)
            f.write("\n")
        written_files.append(str(path))
    return written_files


if __name__ == "__main__":
    raise SystemExit(main())
