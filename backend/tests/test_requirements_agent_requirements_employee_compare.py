from backend.agents.requirements_agent.modules.employee_feature_preprocessing import (
    build_employee_feature_preprocessing_outputs,
)
from backend.agents.requirements_agent.modules.requirements_employee_compare import (
    compare_requirements_to_employee_features,
)


def _requirements_list():
    return {
        "_meta": {"requirements_list_id": "requirements_list_compare_test"},
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
    }


def _roleplay_requirements_input():
    return {
        "required_roles": ["PM", "Backend Developer", "Frontend Developer", "QA Engineer"],
        "required_skills": ["API Design", "React UI", "QA Testing", "Project Planning"],
        "risk_flags": ["integration_risk", "schedule_risk"],
    }


def test_requirements_employee_compare_uses_feature_matrix_before_ranking() -> None:
    feature_outputs = build_employee_feature_preprocessing_outputs("datasets/raw")

    compare = compare_requirements_to_employee_features(
        _requirements_list(),
        _roleplay_requirements_input(),
        feature_outputs["employee_feature_matrix"],
        max_team_size=4,
    )

    assert compare["_meta"]["compare_result_count"] == 100
    assert compare["role_slots"] == [
        "PM",
        "Backend Developer",
        "Frontend Developer",
        "QA Engineer",
    ]
    assert len(compare["compare_results"]) == 100

    first = compare["compare_results"][0]
    assert first["role_comparisons"]
    assert first["best_role"]
    assert 0 <= first["best_role_score"] <= 100
    for role_comparison in first["role_comparisons"]:
        assert 0 <= role_comparison["fit_score"] <= 100
        assert role_comparison["feature_values_used"]
        assert role_comparison["feature_profile"]
