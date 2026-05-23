from backend.agents.requirements_agent.modules.roleplay_handoff_builder import (
    build_roleplay_handoff_manifest,
    build_roleplay_requirements_input,
)
from backend.agents.shadow_roleplay_agent.shadow_roleplay_agent.schemas.simulation_input import (
    RequirementsList as RoleplayRequirementsList,
)


def _requirements_list():
    return {
        "_meta": {
            "requirements_list_id": "requirements_list",
            "project_id": "project_notification",
            "status": "needs_human_confirm",
        },
        "project_name": "Notification Center MVP",
        "project_goal": "Build an in-app notification center for mobile users.",
        "duration_weeks": 4,
        "budget": 50000,
        "required_features": [
            {
                "feature_key": "notification_center",
                "standard_name": "Notification Center",
                "raw_texts": ["Users must review notifications in-app."],
                "confidence": 0.95,
                "status": "system_confirmed",
            },
            {
                "feature_key": "notification_preferences",
                "standard_name": "Notification Preferences",
                "raw_texts": ["Users should control notification categories."],
                "confidence": 0.82,
                "status": "system_confirmed",
            },
        ],
        "required_roles": [
            {
                "role": "Product Manager",
                "source_feature_keys": ["notification_center"],
            },
            {
                "role": "Backend Engineer",
                "source_feature_keys": ["notification_center", "notification_preferences"],
            },
            {
                "role": "Web Frontend Engineer",
                "source_feature_keys": ["notification_center"],
            },
        ],
        "required_skills": [
            {
                "skill": "API Design",
                "source_feature_keys": ["notification_center"],
            },
            {
                "skill": "Push Notification",
                "source_feature_keys": ["notification_center", "notification_preferences"],
            },
        ],
        "constraints": [
            {
                "constraint_key": "short_timeline",
                "text": "The MVP must ship in 4 weeks.",
            }
        ],
        "risk_factors": [
            {
                "risk_key": "integration_risk",
                "text": "Mobile push and backend delivery integration can slip.",
                "source_feature_keys": ["notification_center"],
                "reason": "External push notification dependency.",
            }
        ],
        "selected_employee_columns": [
            {"column_key": "employee.job_category_code", "reason": "Role matching."}
        ],
        "column_weights": {"employee.job_category_code": 1.0},
        "column_priority_order": ["employee.job_category_code"],
        "unknown_requirements": [{"text": "Needs human review."}],
        "missing_extractions": [],
        "missing_fields": [],
        "low_confidence_items": [],
        "invalid_items": [],
    }


def test_build_roleplay_requirements_input_matches_shadow_schema() -> None:
    result = build_roleplay_requirements_input(_requirements_list())

    validated = RoleplayRequirementsList.model_validate(result)

    assert validated.project_id == "project_notification"
    assert validated.required_roles == ["PM", "Backend Developer", "Frontend Developer"]
    assert validated.features[0].feature_id == "notification_center"
    assert validated.features[0].priority == "P0"
    assert validated.features[0].assigned_role == "PM"
    assert "API Design" in validated.features[0].tech_requirements
    assert validated.timeline.total_sprint_days == 20
    assert validated.risk_flags == ["integration_risk"]


def test_build_roleplay_handoff_manifest_marks_remaining_downstream_inputs() -> None:
    requirements = _requirements_list()
    roleplay_input = build_roleplay_requirements_input(requirements)

    manifest = build_roleplay_handoff_manifest(requirements, roleplay_input)

    assert manifest["handoff_status"] == "ready_with_review_items"
    assert manifest["provided_inputs"][0]["recommended_filename"] == "Roleplay_Requirements_Input.json"
    assert {
        item["input_name"] for item in manifest["required_downstream_inputs"]
    } == {
        "selected_team",
        "member_snapshots",
        "team_risk_summary",
        "evidence_metadata",
    }
    assert manifest["review_counts"]["unknown_requirements"] == 1
    assert manifest["roleplay_requirements_summary"]["feature_count"] == 2
