"""CLI runner for local Requirements Agent finish verification."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.agents.requirements_agent.modules.employee_team_ranking import (
    build_employee_team_rankings,
)
from backend.agents.requirements_agent.modules.taxonomy_matcher import load_json
from backend.agents.requirements_agent.pipeline.llm_adapter import (
    SUPPORTED_LLM_MODES,
    LLMConfig,
    build_mapping_suggester,
    build_section_extractor,
)
from backend.agents.requirements_agent.pipeline.local_input_loader import (
    DEFAULT_EMPLOYEE_DATA_DIR,
    DEFAULT_PRD_PATH,
    LocalInputError,
    build_local_project_fields,
    load_local_prd_input,
    read_employee_data_headers,
    validate_employee_column_rules_against_headers,
)
from backend.agents.requirements_agent.pipeline.requirements_pipeline import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REFERENCE_DIR,
    RequirementsPipelineConfig,
    load_references,
    run_requirements_pipeline,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.run_shadow_roleplay_local import (
    DEFAULT_OUTPUT_DIR as DEFAULT_ROLEPLAY_OUTPUT_DIR,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.run_shadow_roleplay_local import (
    SUPPORTED_ROLEPLAY_LLM_MODES,
    run_local_shadow_roleplay_from_packet,
)

JsonObject = dict[str, Any]
ProgressLogger = Callable[[str, Mapping[str, Any]], None]

LOCAL_RANKING_OUTPUT_FILENAMES = {
    "employee_feature_matrix": "Employee_Feature_Matrix.json",
    "employee_feature_metadata": "Employee_Feature_Metadata.json",
    "requirements_employee_compare": "Requirements_Employee_Compare.json",
    "employee_fit_ranking": "Employee_Fit_Ranking.json",
    "team_composition_candidates": "Team_Composition_Candidates.json",
    "team_composition_ranking": "Team_Composition_Ranking.json",
    "roleplay_selected_team_record": "Roleplay_Selected_Team_Record.json",
    "roleplay_employee_fit_profile_snapshots": "Roleplay_Employee_Fit_Profile_Snapshots.json",
    "roleplay_team_risk_summary": "Roleplay_Team_Risk_Summary.json",
    "roleplay_evidence_metadata": "Roleplay_Evidence_Metadata.json",
    "roleplay_simulation_input_packet": "Roleplay_Simulation_Input_Packet.json",
    "roleplay_handoff_manifest": "Roleplay_Handoff_Manifest.json",
}


class LocalRunnerError(RuntimeError):
    """Raised when the local finish runner cannot execute safely."""


def run_local_requirements_agent(
    *,
    prd_path: str | Path = DEFAULT_PRD_PATH,
    employee_data_dir: str | Path = DEFAULT_EMPLOYEE_DATA_DIR,
    llm_mode: str = "stub",
    human_confirm_decision_path: str | Path | None = None,
    project_fields_path: str | Path | None = None,
    write_outputs: bool = False,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    mapping_mode: str = "auto",
    run_roleplay: bool = False,
    roleplay_llm_mode: str = "stub",
    roleplay_strict_llm: bool = False,
    roleplay_output_dir: str | Path = DEFAULT_ROLEPLAY_OUTPUT_DIR,
    roleplay_write_outputs: bool | None = None,
    progress_logger: ProgressLogger | None = None,
) -> JsonObject:
    """Run Requirements Agent locally from PRD and datasets/raw inputs."""

    references = load_references(DEFAULT_REFERENCE_DIR)
    prd_input = load_local_prd_input(prd_path)
    headers = read_employee_data_headers(employee_data_dir)
    column_validation = validate_employee_column_rules_against_headers(
        references["employee_column_rules"],
        headers,
    )
    if column_validation["status"] != "passed":
        raise LocalRunnerError(
            "employee_column_rules.json conflicts with local datasets/raw CSV headers."
        )

    human_confirm_decisions = _load_optional_json(human_confirm_decision_path)
    project_fields = {
        **build_local_project_fields(prd_input.raw_text),
        **_load_optional_json(project_fields_path),
    }
    config = RequirementsPipelineConfig(
        write_outputs=write_outputs,
        output_dir=Path(output_dir),
        human_confirm_complete=bool(human_confirm_decisions.get("human_confirm_complete")),
        progress_logger=progress_logger,
    )
    llm_config = LLMConfig.from_env(mode=llm_mode)
    extractor = build_section_extractor(
        config=llm_config,
        rulebase=references["rulebase"],
    )
    resolved_mapping_mode = _resolve_mapping_mode(mapping_mode, llm_config.mode)
    mapping_suggester = (
        build_mapping_suggester(config=llm_config)
        if resolved_mapping_mode == "llm_assisted"
        else None
    )

    result = run_requirements_pipeline(
        prd_input.raw_text,
        document_id=prd_input.document_id,
        document_type=prd_input.document_type,
        source_uri=prd_input.source_uri,
        project_fields=project_fields,
        human_confirm_decisions=human_confirm_decisions,
        extractor=extractor,
        mapping_mode=resolved_mapping_mode,
        mapping_suggester=mapping_suggester,
        config=config,
    )
    ranking_outputs = _run_local_ranking_bridge(
        result,
        employee_data_dir=employee_data_dir,
        output_dir=output_dir,
        write_outputs=write_outputs,
        progress_logger=progress_logger,
    )
    result["outputs"].update(ranking_outputs)
    if run_roleplay:
        roleplay_result = _run_local_roleplay_bridge(
            result,
            roleplay_llm_mode=roleplay_llm_mode,
            strict_llm=roleplay_strict_llm,
            roleplay_output_dir=roleplay_output_dir,
            write_outputs=write_outputs if roleplay_write_outputs is None else roleplay_write_outputs,
            progress_logger=progress_logger,
        )
        result["roleplay_run"] = {
            "summary": roleplay_result["summary"],
            "written_files": roleplay_result["written_files"],
        }
        result["outputs"]["shadow_roleplay_outputs"] = roleplay_result["outputs"]
    result["local_run"] = {
        "prd_input": {
            "document_id": prd_input.document_id,
            "source_uri": prd_input.source_uri,
            "raw_text_ref": prd_input.raw_text_ref,
            "raw_text_length": len(prd_input.raw_text),
            "extraction": prd_input.extraction,
        },
        "employee_data_dir": str(Path(employee_data_dir)),
        "column_validation": column_validation,
        "llm": llm_config.safe_summary(),
        "mapping_mode": resolved_mapping_mode,
        "summary": build_run_summary(result),
    }
    return result


def build_run_summary(result: Mapping[str, Any]) -> JsonObject:
    outputs = result.get("outputs", {})
    requirements_list = outputs.get("requirements_list", {})
    human_confirm = outputs.get("human_confirm_result", {})
    validation = outputs.get("validation_result", {})
    mapped = outputs.get("mapped_requirements", {})
    roleplay_requirements = outputs.get("roleplay_requirements_input", {})
    feature_matrix = outputs.get("employee_feature_matrix", {})
    feature_metadata = outputs.get("employee_feature_metadata", {})
    compare = outputs.get("requirements_employee_compare", {})
    employee_fit = outputs.get("employee_fit_ranking", {})
    team_candidates = outputs.get("team_composition_candidates", {})
    team_ranking = outputs.get("team_composition_ranking", {})
    selected_team = outputs.get("roleplay_selected_team_record", {})
    roleplay_summary = result.get("roleplay_run", {}).get("summary", {})
    written_files = list(result.get("written_files", []))
    selected_columns = requirements_list.get("selected_employee_columns", [])

    return {
        "pipeline_status": result.get("_meta", {}).get("status"),
        "write_outputs": result.get("_meta", {}).get("write_outputs"),
        "written_file_count": len(written_files),
        "requirements_list_status": requirements_list.get("_meta", {}).get("status"),
        "required_feature_count": len(requirements_list.get("required_features", [])),
        "required_role_count": len(requirements_list.get("required_roles", [])),
        "required_skill_count": len(requirements_list.get("required_skills", [])),
        "selected_column_count": len(selected_columns),
        "unknown_requirement_count": len(mapped.get("unknown_requirements", [])),
        "missing_extraction_count": len(validation.get("missing_extractions", [])),
        "invalid_item_count": len(validation.get("invalid_items", [])),
        "low_confidence_count": len(validation.get("low_confidence_items", [])),
        "human_confirm_complete": human_confirm.get("human_confirm_complete"),
        "roleplay_feature_count": len(roleplay_requirements.get("features", [])),
        "roleplay_required_role_count": len(roleplay_requirements.get("required_roles", [])),
        "roleplay_risk_flag_count": len(roleplay_requirements.get("risk_flags", [])),
        "feature_preprocessing_ready": bool(feature_matrix.get("feature_profiles")),
        "feature_profile_count": len(feature_matrix.get("feature_profiles", [])),
        "feature_key_count": feature_matrix.get("_meta", {}).get("feature_key_count")
        or feature_metadata.get("_meta", {}).get("feature_key_count"),
        "compare_result_count": len(compare.get("compare_results", [])),
        "employee_fit_candidate_count": len(employee_fit.get("employee_rankings", [])),
        "team_composition_candidate_count": len(team_candidates.get("team_candidates", [])),
        "team_candidate_count": len(team_ranking.get("team_rankings", [])),
        "selected_team_id": selected_team.get("team_id"),
        "selected_team_fit_score": selected_team.get("team_fit_score"),
        "roleplay_simulation_input_ready": bool(
            outputs.get("roleplay_simulation_input_packet")
        ),
        "shadow_roleplay_executed": bool(roleplay_summary),
        "shadow_roleplay_status": roleplay_summary.get("roleplay_status"),
        "shadow_roleplay_output_ready": bool(
            outputs.get("shadow_roleplay_outputs", {}).get("simulation_output")
        ),
        "shadow_roleplay_overall_project_fit": roleplay_summary.get("overall_project_fit"),
        "shadow_roleplay_verdict": roleplay_summary.get("verdict"),
        "shadow_roleplay_written_file_count": roleplay_summary.get("written_file_count", 0),
        "shadow_roleplay_actual_llm_mode": roleplay_summary.get("actual_llm_mode"),
        "shadow_roleplay_vertex_turn_count": roleplay_summary.get("vertex_turn_count", 0),
        "shadow_roleplay_fallback_count": roleplay_summary.get("fallback_count", 0),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Requirements Agent locally with PRD and datasets/raw inputs."
    )
    parser.add_argument("--prd", default=str(DEFAULT_PRD_PATH), help="PRD pdf/md/txt/json path.")
    parser.add_argument(
        "--employee-data-dir",
        default=str(DEFAULT_EMPLOYEE_DATA_DIR),
        help="datasets/raw directory path.",
    )
    parser.add_argument(
        "--llm-mode",
        default="stub",
        choices=sorted(SUPPORTED_LLM_MODES),
        help="LLM mode for section extraction.",
    )
    parser.add_argument(
        "--human-confirm-decision",
        default=None,
        help="Optional Human Confirm decision JSON path.",
    )
    parser.add_argument(
        "--project-fields",
        default=None,
        help="Optional project fields JSON path.",
    )
    parser.add_argument(
        "--write-outputs",
        action="store_true",
        help="Write outputs/*.json. Without this, results stay in memory only.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory used when --write-outputs is set.",
    )
    parser.add_argument(
        "--mapping-mode",
        default="auto",
        choices=["auto", "rule", "llm_assisted"],
        help="Taxonomy mapping mode. auto uses LLM-assisted mapping for remote LLM modes.",
    )
    parser.add_argument(
        "--run-roleplay",
        action="store_true",
        help="Run Shadow RolePlay immediately after Requirements Agent handoff packet creation.",
    )
    parser.add_argument(
        "--roleplay-llm-mode",
        default="stub",
        choices=sorted(SUPPORTED_ROLEPLAY_LLM_MODES),
        help="Shadow RolePlay mode used with --run-roleplay.",
    )
    parser.add_argument(
        "--roleplay-strict-llm",
        action="store_true",
        help="Fail RolePlay when remote LLM mode falls back instead of silently using stub.",
    )
    parser.add_argument(
        "--roleplay-output-dir",
        default=str(DEFAULT_ROLEPLAY_OUTPUT_DIR),
        help="Shadow RolePlay output directory used with --run-roleplay and --write-outputs.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress logs. The final JSON summary is still printed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_local_requirements_agent(
            prd_path=args.prd,
            employee_data_dir=args.employee_data_dir,
            llm_mode=args.llm_mode,
            human_confirm_decision_path=args.human_confirm_decision,
            project_fields_path=args.project_fields,
            write_outputs=args.write_outputs,
            output_dir=args.output_dir,
            mapping_mode=args.mapping_mode,
            run_roleplay=args.run_roleplay,
            roleplay_llm_mode=args.roleplay_llm_mode,
            roleplay_strict_llm=args.roleplay_strict_llm,
            roleplay_output_dir=args.roleplay_output_dir,
            progress_logger=None if args.quiet else _make_cli_progress_logger(),
        )
    except (LocalInputError, LocalRunnerError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result["local_run"]["summary"], ensure_ascii=False, indent=2))
    if result.get("written_files"):
        print(json.dumps({"written_files": result["written_files"]}, ensure_ascii=False, indent=2))
    return 0


def _load_optional_json(path: str | Path | None) -> JsonObject:
    if path is None:
        return {}
    return load_json(path)


def _resolve_mapping_mode(mapping_mode: str, llm_mode: str) -> str:
    if mapping_mode != "auto":
        return mapping_mode
    return "rule" if llm_mode == "stub" else "llm_assisted"


def _log_progress(
    progress_logger: ProgressLogger | None,
    event: str,
    **details: Any,
) -> None:
    if progress_logger is not None:
        progress_logger(event, details)


def _run_local_ranking_bridge(
    result: JsonObject,
    *,
    employee_data_dir: str | Path,
    output_dir: str | Path,
    write_outputs: bool,
    progress_logger: ProgressLogger | None,
) -> JsonObject:
    outputs = result["outputs"]
    _log_progress(
        progress_logger,
        "local_ranking_bridge_start",
        employee_data_dir=str(Path(employee_data_dir)),
    )
    ranking_outputs = build_employee_team_rankings(
        outputs["requirements_list"],
        outputs["roleplay_requirements_input"],
        employee_data_dir=employee_data_dir,
    )
    if write_outputs:
        written_files = _write_local_ranking_outputs(ranking_outputs, output_dir)
        existing = list(result.get("written_files", []))
        existing_paths = {str(path) for path in existing}
        for path in written_files:
            if str(path) not in existing_paths:
                existing.append(path)
                existing_paths.add(str(path))
        result["written_files"] = existing
    _log_progress(
        progress_logger,
        "local_ranking_bridge_done",
        feature_profile_count=len(
            ranking_outputs["employee_feature_matrix"].get("feature_profiles", [])
        ),
        compare_result_count=len(
            ranking_outputs["requirements_employee_compare"].get("compare_results", [])
        ),
        employee_count=len(ranking_outputs["employee_fit_ranking"].get("employee_rankings", [])),
        team_candidate_count=len(
            ranking_outputs["team_composition_candidates"].get("team_candidates", [])
        ),
        team_count=len(ranking_outputs["team_composition_ranking"].get("team_rankings", [])),
        selected_team_id=ranking_outputs["roleplay_selected_team_record"].get("team_id"),
    )
    return ranking_outputs


def _run_local_roleplay_bridge(
    result: JsonObject,
    *,
    roleplay_llm_mode: str,
    strict_llm: bool,
    roleplay_output_dir: str | Path,
    write_outputs: bool,
    progress_logger: ProgressLogger | None,
) -> JsonObject:
    packet = result["outputs"].get("roleplay_simulation_input_packet")
    if not packet:
        raise LocalRunnerError("RolePlay input packet is missing from Requirements Agent outputs.")
    _log_progress(
        progress_logger,
        "shadow_roleplay_start",
        llm_mode=roleplay_llm_mode,
        output_dir=str(Path(roleplay_output_dir)),
        write_outputs=write_outputs,
    )
    roleplay_result = run_local_shadow_roleplay_from_packet(
        packet,
        input_packet_label="memory://requirements_agent/roleplay_simulation_input_packet",
        output_dir=roleplay_output_dir,
        llm_mode=roleplay_llm_mode,
        strict_llm=strict_llm,
        write_outputs=write_outputs,
    )
    if write_outputs:
        existing = list(result.get("written_files", []))
        existing_paths = {str(path) for path in existing}
        for path in roleplay_result.get("written_files", []):
            if str(path) not in existing_paths:
                existing.append(path)
                existing_paths.add(str(path))
        result["written_files"] = existing
    summary = roleplay_result["summary"]
    _log_progress(
        progress_logger,
        "shadow_roleplay_done",
        status=summary.get("roleplay_status"),
        phase_count=summary.get("phase_count"),
        scenario_event_count=summary.get("scenario_event_count"),
        verdict=summary.get("verdict"),
        overall_project_fit=summary.get("overall_project_fit"),
        actual_llm_mode=summary.get("actual_llm_mode"),
        fallback_count=summary.get("fallback_count"),
    )
    return roleplay_result


def _write_local_ranking_outputs(
    ranking_outputs: Mapping[str, Any],
    output_dir: str | Path,
) -> list[str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    written_files = []
    for output_key, filename in LOCAL_RANKING_OUTPUT_FILENAMES.items():
        payload = ranking_outputs.get(output_key)
        if payload is None:
            continue
        path = root / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        written_files.append(str(path))
    return written_files


def _make_cli_progress_logger() -> ProgressLogger:
    def log(event: str, details: Mapping[str, Any]) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(
            f"[requirements_agent {timestamp}] {_format_progress_event(event, details)}",
            file=sys.stderr,
            flush=True,
        )

    return log


def _format_progress_event(event: str, details: Mapping[str, Any]) -> str:
    if event == "pipeline_start":
        return (
            "pipeline start "
            f"document_id={details.get('document_id')} "
            f"raw_text_length={details.get('raw_text_length')} "
            f"write_outputs={details.get('write_outputs')}"
        )
    if event == "pipeline_done":
        return (
            "pipeline done "
            f"status={details.get('status')} "
            f"elapsed={details.get('elapsed_seconds')}s"
        )
    if event == "stage_start":
        return _format_stage_event("start", details)
    if event == "stage_done":
        return _format_stage_event("done", details)
    if event == "stage_failed":
        return _format_stage_event("failed", details)
    if event == "document_sections_ready":
        return (
            "sections ready "
            f"section_count={details.get('section_count')} "
            f"token_statuses={details.get('token_check_statuses')}"
        )
    if event == "section_extraction_start":
        return (
            "section extraction start "
            f"section_count={details.get('section_count')} "
            f"document_id={details.get('document_id')}"
        )
    if event == "section_extraction_item_start":
        return (
            "extract section "
            f"{details.get('index')}/{details.get('total')} "
            f"section_id={details.get('section_id')} "
            f"title={_short(details.get('section_title'))} "
            f"tokens={details.get('estimated_tokens')}"
        )
    if event == "section_extraction_item_done":
        return (
            "extract section done "
            f"{details.get('index')}/{details.get('total')} "
            f"section_id={details.get('section_id')} "
            f"elapsed={details.get('elapsed_seconds')}s "
            f"candidates={details.get('candidate_count')} "
            f"confidence={details.get('confidence')}"
        )
    if event == "section_extraction_item_failed":
        return (
            "extract section failed "
            f"{details.get('index')}/{details.get('total')} "
            f"section_id={details.get('section_id')} "
            f"elapsed={details.get('elapsed_seconds')}s "
            f"error={details.get('error')}"
        )
    if event == "section_extraction_merge_start":
        return f"section extraction merge start section_count={details.get('section_count')}"
    if event == "section_extraction_done":
        return (
            "section extraction done "
            f"sections={details.get('section_count')} "
            f"candidates={details.get('candidate_count')} "
            f"merged={details.get('merged_candidate_count')} "
            f"low_confidence={details.get('low_confidence_count')} "
            f"conflicts={details.get('conflict_count')}"
        )
    compact_details = " ".join(f"{key}={value}" for key, value in details.items())
    return f"{event} {compact_details}".strip()


def _format_stage_event(status: str, details: Mapping[str, Any]) -> str:
    stage = details.get("stage")
    parts = [f"stage {status}", f"name={stage}"]
    if "elapsed_seconds" in details:
        parts.append(f"elapsed={details.get('elapsed_seconds')}s")
    if "error" in details:
        parts.append(f"error={details.get('error')}")
    return " ".join(parts)


def _short(value: Any, *, max_length: int = 60) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= max_length:
        return repr(text)
    return repr(text[: max_length - 3] + "...")


if __name__ == "__main__":
    raise SystemExit(main())
