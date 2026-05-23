import json
from pathlib import Path

import pytest

from backend.agents.requirements_agent.modules.employee_team_ranking import (
    build_employee_team_rankings,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.pipeline.run_shadow_roleplay_local import (
    OUTPUT_FILENAMES,
    run_local_shadow_roleplay,
)


def _requirements_list():
    return {
        "_meta": {
            "requirements_list_id": "requirements_list_roleplay_cli_test",
            "project_id": "project_notification",
            "status": "completed",
        },
        "required_roles": [
            {"role": "Product Manager"},
            {"role": "Backend Engineer"},
            {"role": "Web Frontend Engineer"},
            {"role": "QA Engineer"},
        ],
        "required_skills": [
            {"skill": "API Design"},
            {"skill": "React UI"},
            {"skill": "QA Testing"},
            {"skill": "Project Planning"},
        ],
        "risk_factors": [
            {"risk_key": "integration_risk", "text": "FE and BE contract can slip."},
            {"risk_key": "schedule_risk", "text": "Short delivery window."},
        ],
        "column_weights": {
            "employee.job_category_code": 0.35,
            "employee.competency_score": 0.2,
            "jira_activity.sprint_completion_rate": 0.15,
            "jira_activity.completed_issue_count": 0.15,
            "calendar_activity.busy_minutes": 0.15,
        },
        "column_priority_order": [
            "employee.job_category_code",
            "employee.competency_score",
            "jira_activity.sprint_completion_rate",
            "calendar_activity.busy_minutes",
        ],
        "unknown_requirements": [],
        "missing_extractions": [],
        "missing_fields": [],
        "low_confidence_items": [],
        "invalid_items": [],
    }


def _roleplay_requirements_input():
    return {
        "project_id": "project_notification",
        "project_name": "Notification Center MVP",
        "project_summary": "Build notification center.",
        "required_roles": ["PM", "Backend Developer", "Frontend Developer", "QA Engineer"],
        "required_skills": ["API Design", "React UI", "QA Testing", "Project Planning"],
        "features": [
            {
                "feature_id": "notification_center",
                "feature_name": "Notification Center",
                "priority": "P0",
                "assigned_role": "Backend Developer",
                "tech_requirements": ["API Design", "React UI"],
                "dependencies": [],
                "estimated_days": 3,
                "risk_notes": "integration_risk",
            }
        ],
        "timeline": {
            "total_sprint_days": 20,
            "milestones": [
                {
                    "name": "Notification Center complete",
                    "due_day": 10,
                    "owner_role": "Backend Developer",
                }
            ],
        },
        "constraints": ["Ship in 4 weeks."],
        "risk_flags": ["integration_risk", "schedule_risk"],
    }


def _write_roleplay_packet(tmp_path) -> Path:
    ranking_result = build_employee_team_rankings(
        _requirements_list(),
        _roleplay_requirements_input(),
        employee_data_dir="datasets/raw",
        max_team_size=4,
        top_candidates_per_role=3,
        max_ranked_teams=5,
        simulation_id="sim_roleplay_cli_test",
    )
    packet_path = tmp_path / "Roleplay_Simulation_Input_Packet.json"
    packet_path.write_text(
        json.dumps(
            ranking_result["roleplay_simulation_input_packet"],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return packet_path


def test_shadow_roleplay_local_runner_writes_final_outputs(tmp_path) -> None:
    packet_path = _write_roleplay_packet(tmp_path)
    output_dir = tmp_path / "roleplay_outputs"

    result = run_local_shadow_roleplay(
        input_packet_path=packet_path,
        output_dir=output_dir,
        llm_mode="stub",
        write_outputs=True,
    )

    summary = result["summary"]
    assert summary["roleplay_status"] == "completed"
    assert summary["phase_count"] == 5
    assert summary["scenario_event_count"] > 0
    assert summary["written_file_count"] == len(OUTPUT_FILENAMES)
    assert (Path(output_dir) / "Simulation_OUTPUT.json").exists()


def test_shadow_roleplay_vertex_non_strict_records_stub_fallback(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "")
    packet_path = _write_roleplay_packet(tmp_path)

    result = run_local_shadow_roleplay(
        input_packet_path=packet_path,
        output_dir=tmp_path / "roleplay_outputs",
        llm_mode="vertex",
        write_outputs=False,
    )

    summary = result["summary"]
    assert summary["actual_llm_mode"] == "mixed_fallback"
    assert summary["vertex_turn_count"] == 0
    assert summary["fallback_count"] > 0


def test_shadow_roleplay_vertex_strict_fails_without_project(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GCP_PROJECT_ID", "")
    packet_path = _write_roleplay_packet(tmp_path)

    with pytest.raises(RuntimeError, match="strict Vertex RolePlay"):
        run_local_shadow_roleplay(
            input_packet_path=packet_path,
            output_dir=tmp_path / "roleplay_outputs",
            llm_mode="vertex",
            strict_llm=True,
            write_outputs=False,
        )
