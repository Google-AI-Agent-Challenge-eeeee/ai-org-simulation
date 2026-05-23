from backend.agents.requirements_agent.modules.employee_team_ranking import (
    build_employee_team_rankings,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    EmployeeFitProfileSnapshot,
    EvidenceMetadata,
    SelectedTeamRecord,
    SimulationInputPacket,
    TeamRiskSummary,
)


def _requirements_list():
    return {
        "_meta": {
            "requirements_list_id": "requirements_list_test",
            "project_id": "project_notification",
            "status": "completed",
        },
        "required_roles": [
            {"role": "Product Manager", "source_feature_keys": ["notification_center"]},
            {"role": "Backend Engineer", "source_feature_keys": ["notification_center"]},
            {"role": "Web Frontend Engineer", "source_feature_keys": ["notification_center"]},
            {"role": "QA Engineer", "source_feature_keys": ["notification_center"]},
        ],
        "required_skills": [
            {"skill": "API Design", "source_feature_keys": ["notification_center"]},
            {"skill": "React UI", "source_feature_keys": ["notification_center"]},
            {"skill": "QA Testing", "source_feature_keys": ["notification_center"]},
            {"skill": "Project Planning", "source_feature_keys": ["notification_center"]},
        ],
        "risk_factors": [
            {
                "risk_key": "integration_risk",
                "text": "FE and BE contract can slip.",
                "source_feature_keys": ["notification_center"],
            },
            {
                "risk_key": "schedule_risk",
                "text": "Short delivery window.",
                "source_feature_keys": ["notification_center"],
            },
        ],
        "selected_employee_columns": [
            {"column_key": "employee.job_category_code"},
            {"column_key": "jira_activity.sprint_completion_rate"},
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


def test_build_employee_team_rankings_generates_roleplay_ready_inputs() -> None:
    result = build_employee_team_rankings(
        _requirements_list(),
        _roleplay_requirements_input(),
        employee_data_dir="datasets/raw",
        max_team_size=4,
        top_candidates_per_role=3,
        max_ranked_teams=5,
    )

    assert result["employee_feature_matrix"]["feature_profiles"]
    assert result["employee_feature_metadata"]["features"]
    assert result["requirements_employee_compare"]["compare_results"]
    assert result["team_composition_candidates"]["team_candidates"]
    assert result["employee_fit_ranking"]["employee_rankings"]
    ranking_meta = result["employee_fit_ranking"]["_meta"]
    assert ranking_meta["source_employee_count"] == 100
    assert ranking_meta["candidate_employee_count"] < ranking_meta["source_employee_count"]
    assert ranking_meta["role_candidate_counts"]["Backend Developer"] == 18
    assert ranking_meta["role_candidate_counts"]["Frontend Developer"] == 18
    assert ranking_meta["role_candidate_counts"]["QA Engineer"] == 18
    assert ranking_meta["role_candidate_counts"]["PM"] < ranking_meta["source_employee_count"]
    assert all(
        set(employee["candidate_roles"]).issubset(
            {"PM", "Backend Developer", "Frontend Developer", "QA Engineer"}
        )
        for employee in result["employee_fit_ranking"]["employee_rankings"]
    )
    assert len(result["team_composition_ranking"]["team_rankings"]) <= 5
    assert result["roleplay_handoff_manifest"]["handoff_status"] == "roleplay_input_packet_ready"

    SelectedTeamRecord.model_validate(result["roleplay_selected_team_record"])
    TeamRiskSummary.model_validate(result["roleplay_team_risk_summary"])
    for snapshot in result["roleplay_employee_fit_profile_snapshots"]:
        EmployeeFitProfileSnapshot.model_validate(snapshot)
    for evidence in result["roleplay_evidence_metadata"]:
        EvidenceMetadata.model_validate(evidence)
    SimulationInputPacket.model_validate(result["roleplay_simulation_input_packet"])

    selected_members = result["roleplay_selected_team_record"]["members"]
    assert len({member["employee_id"] for member in selected_members}) == len(selected_members)
    assert result["roleplay_team_risk_summary"]["risk_prior_scores"]
